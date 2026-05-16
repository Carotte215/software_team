import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import Honor
from app.schemas import HonorCreate
from app.services.common import audit, uid
from app.services.permissions import TEACHER, require_roles
from app.services.serializers import honor

router = APIRouter(prefix="/honors", tags=["honors"])


@router.get("")
def list_honors(
    year: str = "",
    major: str = "",
    category: str = "",
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    stmt = select(Honor)
    if year:
        stmt = stmt.where(Honor.year == int(year))
    if major:
        stmt = stmt.where(Honor.major.ilike(f"%{major}%"))
    if category:
        stmt = stmt.where(Honor.category == category)
    rows = db.scalars(stmt.order_by(Honor.year.desc())).all()
    meta = read_honor_meta()
    return {"list": [honor_with_meta(row, meta.get(row.id, {}), session.role) for row in rows]}


@router.post("")
def create_honor(payload: HonorCreate, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    require_roles(session, TEACHER)
    row = Honor(id=uid("honor"), **payload.model_dump(exclude={"attachments", "visibility"}))
    db.add(row)
    save_honor_meta(row.id, payload)
    audit(db, session, "honor_create", row.id)
    db.commit()
    return honor_with_meta(row, read_honor_meta().get(row.id, {}), session.role)


@router.put("/{honor_id}")
def update_honor(honor_id: str, payload: HonorCreate, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    require_roles(session, TEACHER)
    row = db.get(Honor, honor_id)
    if not row:
        raise HTTPException(status_code=404, detail="honor not found")
    for key, value in payload.model_dump(exclude={"attachments", "visibility"}).items():
        setattr(row, key, value)
    save_honor_meta(honor_id, payload)
    audit(db, session, "honor_update", honor_id)
    db.commit()
    return honor_with_meta(row, read_honor_meta().get(row.id, {}), session.role)


def honor_meta_path() -> Path:
    path = Path(get_settings().upload_dir).parent / "honor_meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def read_honor_meta() -> dict:
    path = honor_meta_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_honor_meta(data: dict) -> None:
    honor_meta_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_honor_meta(honor_id: str, payload: HonorCreate) -> None:
    data = read_honor_meta()
    data[honor_id] = {
        "visibility": payload.visibility if payload.visibility in {"public", "restricted"} else "public",
        "attachments": normalize_attachments(payload.attachments, payload.visibility),
    }
    write_honor_meta(data)


def normalize_attachments(attachments: list[dict], visibility: str) -> list[dict]:
    allowed = visibility if visibility in {"public", "restricted"} else "public"
    result = []
    for item in attachments or []:
        result.append({**item, "visibility": item.get("visibility") or allowed})
    return result


def honor_with_meta(row: Honor, meta: dict, role: str) -> dict:
    payload = honor(row)
    visibility = meta.get("visibility", "public")
    attachments = meta.get("attachments", [])
    if role not in {"teacher", "leader"}:
        attachments = [item for item in attachments if item.get("visibility") != "restricted"]
    payload.update({"visibility": visibility, "attachments": attachments})
    return payload
