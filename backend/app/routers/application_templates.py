from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import ApplicationTemplate
from app.schemas import ApplicationTemplateCreate, ApplicationTemplateUpdate
from app.services.common import audit, uid
from app.services.permissions import TEACHER, require_roles

router = APIRouter(prefix="/workbench/application-templates", tags=["application-templates"])


@router.get("")
def list_templates(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    require_roles(session, TEACHER)
    rows = db.scalars(select(ApplicationTemplate).order_by(ApplicationTemplate.apply_type, ApplicationTemplate.name)).all()
    return {"list": [template_dict(row) for row in rows]}


@router.post("")
def create_template(
    payload: ApplicationTemplateCreate,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    require_roles(session, TEACHER)
    row = ApplicationTemplate(
        id=uid("tpl"),
        name=payload.name,
        apply_type=payload.apply_type,
        subtype=payload.subtype,
        body_html=payload.body_html,
    )
    db.add(row)
    audit(db, session, "application_template_create", row.id)
    db.commit()
    return template_dict(row)


@router.put("/{template_id}")
def update_template(
    template_id: str,
    payload: ApplicationTemplateUpdate,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    require_roles(session, TEACHER)
    row = db.get(ApplicationTemplate, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="template not found")
    row.name = payload.name
    row.apply_type = payload.apply_type
    row.subtype = payload.subtype
    row.body_html = payload.body_html
    audit(db, session, "application_template_update", template_id)
    db.commit()
    return template_dict(row)


@router.delete("/{template_id}")
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    require_roles(session, TEACHER)
    row = db.get(ApplicationTemplate, template_id)
    if not row:
        raise HTTPException(status_code=404, detail="template not found")
    db.delete(row)
    audit(db, session, "application_template_delete", template_id)
    db.commit()
    return {"ok": True}


def template_dict(row: ApplicationTemplate) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "applyType": row.apply_type,
        "subtype": row.subtype,
        "bodyHtml": row.body_html,
    }


def find_template(db: Session, apply_type: str, subtype: str = "") -> ApplicationTemplate | None:
    rows = db.scalars(
        select(ApplicationTemplate).where(ApplicationTemplate.apply_type == apply_type),
    ).all()
    if subtype:
        exact = next((r for r in rows if r.subtype == subtype), None)
        if exact:
            return exact
    return rows[0] if rows else None
