from dataclasses import dataclass

from fastapi import Header, HTTPException

from app.core.config import get_settings
from app.services.auth_tokens import verify_token


@dataclass(frozen=True)
class CurrentSession:
    student_id: str
    role: str
    token: str = ""


def get_current_session(
    x_student_id: str = Header(default=""),
    x_role: str = Header(default="student"),
    authorization: str = Header(default=""),
) -> CurrentSession:
    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token)
    if payload:
        return CurrentSession(student_id=payload["studentId"], role=payload["role"], token=token)

    settings = get_settings()
    if settings.auth_mode == "token":
        raise HTTPException(status_code=401, detail="invalid or missing token")

    student_id = x_student_id or "2024201581"
    return CurrentSession(student_id=student_id, role=x_role or "student", token=token)
