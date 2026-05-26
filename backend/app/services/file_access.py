"""文件下载/预览的业务级鉴权。"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentSession
from app.models import Application, Honor, KnowledgeItem


def assert_file_access(db: Session, session: CurrentSession, file_id: str, meta: dict) -> None:
    if session.role in {"teacher", "leader"}:
        return

    uploader = meta.get("uploadedBy", "")
    if uploader and uploader == session.student_id:
        return

    business = meta.get("business", "general")

    if business == "honor":
        if _honor_allows_file(db, file_id, session):
            return
        raise HTTPException(status_code=403, detail="honor attachment forbidden")

    if business == "knowledge":
        if _knowledge_allows_file(db, file_id):
            return
        raise HTTPException(status_code=403, detail="knowledge attachment forbidden")

    if business == "application":
        if _application_allows_file(db, file_id, session):
            return
        raise HTTPException(status_code=403, detail="application attachment forbidden")

    if uploader and uploader != session.student_id:
        raise HTTPException(status_code=403, detail="forbidden")


def _file_in_attachments(attachments: list[dict] | None, file_id: str) -> bool:
    for item in attachments or []:
        if item.get("id") == file_id or item.get("fileId") == file_id:
            return True
    return False


def _honor_allows_file(db: Session, file_id: str, session: CurrentSession) -> bool:
    for row in db.scalars(select(Honor)).all():
        if not _file_in_attachments(row.attachments, file_id):
            continue
        if row.online is False:
            return False
        if row.visibility == "restricted":
            return session.role in {"teacher", "leader"}
        return True
    return False


def _knowledge_allows_file(db: Session, file_id: str) -> bool:
    for row in db.scalars(select(KnowledgeItem).where(KnowledgeItem.online.is_(True))).all():
        if _file_in_attachments(row.attachments, file_id):
            return True
    return False


def _application_allows_file(db: Session, file_id: str, session: CurrentSession) -> bool:
    for row in db.scalars(select(Application).where(Application.student_id == session.student_id)).all():
        if _file_in_attachments(row.attachments, file_id):
            return True
    return False
