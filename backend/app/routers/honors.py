from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import or_, select

from sqlalchemy.orm import Session



from app.db.session import get_db

from app.deps import CurrentSession, get_current_session

from app.models import Honor

from app.schemas import HonorCreate, HonorOnlinePut

from app.services.common import audit, uid

from app.services.permissions import COORDINATOR, LEADER, TEACHER, require_roles

from app.services.serializers import honor_public



router = APIRouter(prefix="/honors", tags=["honors"])





@router.get("")

def list_honors(

    year: str = "",

    major: str = "",

    category: str = "",

    q: str = "",

    include_offline: bool = False,

    db: Session = Depends(get_db),

    session: CurrentSession = Depends(get_current_session),

) -> dict:

    stmt = select(Honor)

    if session.role in {"student", "coordinator"} and not include_offline:

        stmt = stmt.where(Honor.online.is_(True))

    elif include_offline and session.role not in {TEACHER, LEADER}:

        raise HTTPException(status_code=403, detail="forbidden")

    if year:

        stmt = stmt.where(Honor.year == int(year))

    if major:

        stmt = stmt.where(Honor.major.ilike(f"%{major}%"))

    if category:

        stmt = stmt.where(Honor.category == category)

    if q:

        stmt = stmt.where(or_(Honor.title.ilike(f"%{q}%"), Honor.winner.ilike(f"%{q}%")))

    rows = db.scalars(stmt.order_by(Honor.year.desc())).all()

    return {"list": [honor_public(row, session.role) for row in rows]}





@router.post("")

def create_honor(payload: HonorCreate, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    require_roles(session, TEACHER)

    row = Honor(

        id=uid("honor"),

        title=payload.title,

        winner=payload.winner,

        year=payload.year,

        major=payload.major,

        grade=payload.grade,

        category=payload.category,

        intro=payload.intro,

        visibility=payload.visibility if payload.visibility in {"public", "restricted"} else "public",

        online=payload.online is not False,

        attachments=normalize_attachments(payload.attachments, payload.visibility),

    )

    db.add(row)

    audit(db, session, "honor_create", row.id)

    db.commit()

    return honor_public(row, session.role)





@router.put("/{honor_id}")

def update_honor(honor_id: str, payload: HonorCreate, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    require_roles(session, TEACHER)

    row = db.get(Honor, honor_id)

    if not row:

        raise HTTPException(status_code=404, detail="honor not found")

    row.title = payload.title

    row.winner = payload.winner

    row.year = payload.year

    row.major = payload.major

    row.grade = payload.grade

    row.category = payload.category

    row.intro = payload.intro

    row.visibility = payload.visibility if payload.visibility in {"public", "restricted"} else "public"

    row.online = payload.online is not False

    row.attachments = normalize_attachments(payload.attachments, payload.visibility)

    audit(db, session, "honor_update", honor_id)

    db.commit()

    return honor_public(row, session.role)





@router.post("/{honor_id}/online")

def set_honor_online(

    honor_id: str,

    payload: HonorOnlinePut,

    db: Session = Depends(get_db),

    session: CurrentSession = Depends(get_current_session),

) -> dict:

    require_roles(session, TEACHER)

    row = db.get(Honor, honor_id)

    if not row:

        raise HTTPException(status_code=404, detail="honor not found")

    row.online = payload.online

    audit(db, session, "honor_online" if payload.online else "honor_offline", honor_id)

    db.commit()

    return honor_public(row, session.role)





@router.delete("/{honor_id}")

def delete_honor(honor_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    require_roles(session, TEACHER)

    row = db.get(Honor, honor_id)

    if not row:

        raise HTTPException(status_code=404, detail="honor not found")

    db.delete(row)

    audit(db, session, "honor_delete", honor_id)

    db.commit()

    return {"ok": True, "id": honor_id}





def normalize_attachments(attachments: list[dict], visibility: str) -> list[dict]:

    allowed = visibility if visibility in {"public", "restricted"} else "public"

    return [{**item, "visibility": item.get("visibility") or allowed} for item in attachments or []]


