from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.db.session import engine
from app.deps import CurrentSession, get_current_session
from app.services.db_health import ping_database
from app.services.message_channels import smtp_enabled

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    db_ok, db_detail = ping_database(engine)
    return {
        "ok": db_ok,
        "database": "up" if db_ok else "down",
        "databaseDetail": db_detail[:120] if db_detail else "",
        "smtpConfigured": smtp_enabled(),
    }


@router.get("/api/runtime")
def runtime() -> dict:
    settings = get_settings()
    db_ok, _ = ping_database(engine)
    dialect = "kingbase" if "kingbase" in settings.database_url.lower() else "postgresql"
    return {
        "ok": True,
        "appName": settings.app_name,
        "env": settings.app_env,
        "authMode": settings.auth_mode,
        "tokenHours": settings.auth_token_hours,
        "maxUploadBytes": settings.max_upload_bytes,
        "autoCreateTables": settings.auto_create_tables,
        "databaseDialect": dialect,
        "databaseUp": db_ok,
        "schedulerEnabled": settings.enable_scheduler,
    }


@router.get("/api/session")
def session_info(session: CurrentSession = Depends(get_current_session)) -> dict:
    return {
        "studentId": session.student_id,
        "role": session.role,
        "authMode": get_settings().auth_mode,
        "hasToken": bool(session.token),
    }
