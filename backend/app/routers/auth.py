from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import Student
from app.schemas import ChangePasswordRequest, LoginRequest, PasswordResetRequest
from app.services.auth_tokens import issue_token, verify_token
from app.services.common import audit
from app.services.passwords import default_initial_password, verify_password
from app.services.permissions import COORDINATOR, LEADER, STUDENT, TEACHER, require_roles
from app.services.serializers import student_public

router = APIRouter(prefix="/auth", tags=["auth"])

VALID_ROLES = {STUDENT, TEACHER, COORDINATOR, LEADER}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=401, detail="unknown identity")
    if not payload.password:
        raise HTTPException(status_code=401, detail="password required")

    role = (student.role or STUDENT).strip() or STUDENT
    if role not in VALID_ROLES:
        raise HTTPException(status_code=500, detail="account role invalid")

    if student.password_hash:
        if not verify_password(payload.password, student.password_hash):
            raise HTTPException(status_code=401, detail="invalid credential")
    elif get_settings().auth_mode != "token":
        if payload.password != get_settings().auth_demo_password:
            raise HTTPException(status_code=401, detail="invalid credential")
    else:
        expected = default_initial_password(student.student_id)
        if payload.password != expected:
            raise HTTPException(status_code=401, detail="invalid credential")

    token = issue_token(payload.student_id, role)
    audit(
        db,
        CurrentSession(student_id=payload.student_id, role=role, token=token),
        "auth_login",
        payload.student_id,
        {"role": role},
    )
    db.commit()
    return {
        "token": token,
        "studentId": payload.student_id,
        "role": role,
        "student": student_public(student, role),
        "expiresInHours": get_settings().auth_token_hours,
    }


@router.post("/reset-password")
def reset_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    from app.services.passwords import hash_password

    require_roles(session, TEACHER)
    row = db.get(Student, payload.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="student not found")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="password too short")
    row.password_hash = hash_password(payload.new_password)
    audit(db, session, "auth_reset_password", row.student_id)
    db.commit()
    return {"ok": True, "studentId": row.student_id}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    from app.services.passwords import hash_password, verify_password

    row = db.get(Student, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="student not found")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="password too short")
    if row.password_hash:
        if not verify_password(payload.old_password, row.password_hash):
            raise HTTPException(status_code=401, detail="invalid old password")
    elif payload.old_password != default_initial_password(row.student_id):
        raise HTTPException(status_code=401, detail="invalid old password")
    row.password_hash = hash_password(payload.new_password)
    audit(db, session, "auth_change_password", row.student_id)
    db.commit()
    return {"ok": True}


@router.post("/refresh")
def refresh_token(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    payload = verify_token(session.token)
    if not payload:
        raise HTTPException(status_code=401, detail="invalid token")
    student = db.get(Student, session.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="student not found")
    role = (student.role or STUDENT).strip() or STUDENT
    if role not in VALID_ROLES:
        raise HTTPException(status_code=500, detail="account role invalid")
    token = issue_token(session.student_id, role)
    return {
        "token": token,
        "studentId": session.student_id,
        "role": role,
        "expiresInHours": get_settings().auth_token_hours,
    }
