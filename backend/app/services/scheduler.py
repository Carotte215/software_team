import logging
import os
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _dispatch_scheduled_notices() -> None:
    from app.db.session import SessionLocal
    from app.deps import CurrentSession
    from app.routers.notices import run_scheduled_dispatch
    from app.services.permissions import TEACHER

    db = SessionLocal()
    try:
        run_scheduled_dispatch(db, CurrentSession(student_id="system", role=TEACHER, token=""))
        db.commit()
    except Exception:
        logger.exception("scheduled notice dispatch failed")
        db.rollback()
    finally:
        db.close()


def _refresh_party_reminders() -> None:
    from app.db.session import SessionLocal
    from app.deps import CurrentSession
    from app.routers.party import run_party_reminders
    from app.services.permissions import TEACHER

    db = SessionLocal()
    try:
        run_party_reminders(db, CurrentSession(student_id="system", role=TEACHER, token=""))
        db.commit()
    except Exception:
        logger.exception("party reminder refresh failed")
        db.rollback()
    finally:
        db.close()


def _refresh_league_reminders() -> None:
    from app.db.session import SessionLocal
    from app.deps import CurrentSession
    from app.routers.league import run_league_reminders
    from app.services.permissions import TEACHER

    db = SessionLocal()
    try:
        run_league_reminders(db, CurrentSession(student_id="system", role=TEACHER, token=""))
        db.commit()
    except Exception:
        logger.exception("league reminder refresh failed")
        db.rollback()
    finally:
        db.close()


def start_schedulers() -> None:
    global _scheduler
    if os.getenv("ENABLE_SCHEDULER", "true").lower() not in {"1", "true", "yes"}:
        return
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(_dispatch_scheduled_notices, "interval", minutes=5, id="notice_dispatch")
    _scheduler.add_job(_refresh_party_reminders, "interval", hours=6, id="party_reminders")
    _scheduler.add_job(_refresh_league_reminders, "interval", hours=6, id="league_reminders")
    _scheduler.start()
    logger.info("background schedulers started")
