import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import TemplateFile
from app.services.common import audit, uid
from app.services.file_access import assert_file_access
from app.services.file_storage import data_path, meta_path, storage_root

router = APIRouter(tags=["files"])

BLOCKED_SUFFIXES = {".exe", ".bat", ".cmd", ".sh", ".js", ".msi"}
ALLOWED_BUSINESSES = {"general", "knowledge", "honor", "application", "template", "party", "league"}


def safe_suffix(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in BLOCKED_SUFFIXES:
        raise HTTPException(status_code=400, detail="unsupported file type")
    return suffix


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    business: str = Form(default="general"),
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    if business not in ALLOWED_BUSINESSES:
        raise HTTPException(status_code=400, detail="unsupported business type")
    suffix = safe_suffix(file.filename or "")
    file_id = uid("file")
    target = data_path(file_id, suffix)
    size = 0
    max_size = get_settings().max_upload_bytes
    with target.open("wb") as fp:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_size:
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="file exceeds 30MB limit")
            fp.write(chunk)

    meta = {
        "id": file_id,
        "name": file.filename or f"{file_id}{suffix}",
        "size": size,
        "contentType": file.content_type or "application/octet-stream",
        "business": business,
        "suffix": suffix,
        "url": f"/api/files/{file_id}/download",
        "uploadedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
        "uploadedBy": session.student_id,
    }
    meta_path(file_id).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    audit(db, session, "file_upload", file_id, {"business": business, "size": size})
    db.commit()
    return meta


@router.get("/files/{file_id}/download")
def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> FileResponse:
    meta_file = meta_path(file_id)
    if not meta_file.exists():
        raise HTTPException(status_code=404, detail="file not found")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert_file_access(db, session, file_id, meta)
    target = data_path(file_id, meta.get("suffix", ""))
    if not target.exists():
        raise HTTPException(status_code=404, detail="file not found")
    audit(db, session, "file_download", file_id, {"business": meta.get("business", "general")})
    db.commit()
    return FileResponse(target, media_type=meta.get("contentType") or "application/octet-stream", filename=meta.get("name") or target.name)


PREVIEW_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".txt": "text/plain; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
}


@router.get("/files/{file_id}/preview")
def preview_file(
    file_id: str,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> FileResponse:
    meta_file = meta_path(file_id)
    if not meta_file.exists():
        raise HTTPException(status_code=404, detail="file not found")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert_file_access(db, session, file_id, meta)
    suffix = meta.get("suffix", "").lower()
    if suffix not in PREVIEW_TYPES:
        raise HTTPException(status_code=415, detail="preview not supported for this file type")
    target = data_path(file_id, suffix)
    if not target.exists():
        raise HTTPException(status_code=404, detail="file not found")
    media_type = PREVIEW_TYPES[suffix]
    audit(db, session, "file_preview", file_id, {"business": meta.get("business", "general")})
    db.commit()
    return FileResponse(target, media_type=media_type, filename=meta.get("name") or target.name)


@router.get("/templates/{template_id}/download")
def download_template(template_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> Response:
    row = db.get(TemplateFile, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="template not found")
    if not row.file_id:
        raise HTTPException(status_code=409, detail="template file not uploaded")
    meta_file = meta_path(row.file_id)
    if not meta_file.exists():
        raise HTTPException(status_code=409, detail="template metadata missing")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    target = data_path(row.file_id, meta.get("suffix", ""))
    if not target.exists():
        raise HTTPException(status_code=409, detail="template file missing")
    audit(db, session, "template_download", template_id)
    db.commit()
    return FileResponse(
        target,
        media_type=meta.get("contentType") or "application/octet-stream",
        filename=meta.get("name") or row.name,
    )
