from sqlalchemy import text
from sqlalchemy.engine import Engine


def ping_database(engine: Engine) -> tuple[bool, str]:
    try:
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
        return True, str(version or "")
    except Exception as exc:
        return False, str(exc)
