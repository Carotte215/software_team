from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import TemplateFile
from app.schemas import TemplateFileCreate, TemplateFileUpdate
from app.services.common import audit, uid
from app.services.file_storage import cleanup_orphan_files
from app.services.permissions import COORDINATOR, TEACHER, require_roles
from app.services.serializers import template

router = APIRouter(prefix="/workbench/templates", tags=["templates"])


@router.get("")
def list_templates(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    require_roles(session, TEACHER, COORDINATOR)
    rows = db.scalars(select(TemplateFile).order_by(TemplateFile.scene, TemplateFile.name)).all()
    return {"list": [template(row) for row in rows]}


@router.post("")
def create_template(
    payload: TemplateFileCreate,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    require_roles(session, TEACHER, COORDINATOR)
    row = TemplateFile(
        id=uid("tpl"),
        name=payload.name,
        scene=payload.scene,
        format=payload.format,
        file_url=payload.file_url,
        file_id=payload.file_id,
    )
    db.add(row)
    audit(db, session, "template_create", row.id)
    db.commit()
    return template(row)


@router.put("/{template_id}")
def update_template(
    template_id: str,
    payload: TemplateFileUpdate,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    require_roles(session, TEACHER, COORDINATOR)
    row = db.get(TemplateFile, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="template not found")
    old_file_id = row.file_id
    row.name = payload.name
    row.scene = payload.scene
    row.format = payload.format
    row.file_url = payload.file_url
    row.file_id = payload.file_id
    audit(db, session, "template_update", template_id)
    db.commit()
    cleanup_orphan_files(db, {old_file_id} if old_file_id and old_file_id != row.file_id else set())
    return template(row)


@router.delete("/{template_id}")
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    require_roles(session, TEACHER)
    row = db.get(TemplateFile, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="template not found")
    file_id = row.file_id
    db.delete(row)
    audit(db, session, "template_delete", template_id)
    db.commit()
    cleanup_orphan_files(db, {file_id} if file_id else set())
    return {"ok": True}
