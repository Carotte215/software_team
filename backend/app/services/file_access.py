"""文件下载/预览的业务级鉴权。"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import CurrentSession
from app.models import Application, Honor, KnowledgeItem, LeagueProgress, PartyProgress
from app.services.permissions import COORDINATOR, scoped_student_ids


def assert_file_access(db: Session, session: CurrentSession, file_id: str, meta: dict) -> None:
    if session.role in {"teacher", "leader"}:
        return

    uploader = meta.get("uploadedBy", "")
    if uploader and uploader == session.student_id:
        return

    business = meta.get("business", "general")
    allowed_business = {"general", "honor", "knowledge", "application", "template", "party", "league"}
    if business not in allowed_business:
        raise HTTPException(status_code=403, detail="unknown file business")

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

    if business == "template":
        return

    if business in {"party", "league"}:
        if _party_material_allows_file(db, file_id, session, league=business == "league"):
            return
        raise HTTPException(status_code=403, detail="party material forbidden")

    if uploader and uploader != session.student_id:
        raise HTTPException(status_code=403, detail="forbidden")


def _file_in_attachments(attachments: list[dict] | None, file_id: str) -> bool:
    for item in attachments or []:
        if item.get("id") == file_id or item.get("fileId") == file_id:
            return True
    return False


def _party_material_allows_file(db: Session, file_id: str, session: CurrentSession, *, league: bool = False) -> bool:
    model = LeagueProgress if league else PartyProgress
    if session.role in {"teacher", "leader"}:
        return db.scalars(select(model)).first() is not None
    row = db.get(model, session.student_id)
    if not row:
        return False
    from app.services.party_materials import collect_step_file_ids

    return file_id in collect_step_file_ids(row)


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
    stmt = select(Application)
    if session.role == COORDINATOR:
        scope_ids = scoped_student_ids(db, session)
        if scope_ids is None:
            return False
        stmt = stmt.where(Application.student_id.in_(scope_ids))
    else:
        stmt = stmt.where(Application.student_id == session.student_id)
    for row in db.scalars(stmt).all():
        if _file_in_attachments(row.attachments, file_id):
            return True
    return False
