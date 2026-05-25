import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import PartyProgress
from app.services.common import audit, now_ms
from app.services.seed_data import FLOW_STAGES
from app.services.serializers import party

router = APIRouter(tags=["party"])

DEFAULT_TIMELINE_RULES = [
    {"stageKey": "applicant", "durationDays": 30, "remindBeforeDays": 7, "material": "入党申请书、谈话记录"},
    {"stageKey": "activist", "durationDays": 365, "remindBeforeDays": 30, "material": "培养考察登记表、思想汇报"},
    {"stageKey": "candidate", "durationDays": 90, "remindBeforeDays": 14, "material": "政审材料、公示记录、培训结业材料"},
    {"stageKey": "probationary", "durationDays": 365, "remindBeforeDays": 30, "material": "预备党员考察表、转正申请"},
    {"stageKey": "member", "durationDays": 0, "remindBeforeDays": 0, "material": "归档材料"},
]


@router.get("/party/progress")
def progress(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    return {"flowName": "入党流程", "stages": FLOW_STAGES, "timelineRules": timeline_rules(), **party(row)}


@router.post("/party/tasks/{task_id}/done")
def complete_task(task_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    row.tasks = [{**task, "done": True} if task.get("id") == task_id else task for task in row.tasks]
    audit(db, session, "party_task_done", task_id)
    db.commit()
    return {"ok": True}


@router.post("/workbench/party/advance")
def advance(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    row = db.get(PartyProgress, payload.get("studentId"))
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    row.current_key = payload.get("nextKey", row.current_key)
    row.history = [*row.history, {"stageKey": row.current_key, "at": now_ms(), "remark": payload.get("remark", "管理端推进阶段")}]
    ensure_timeline_task(row)
    audit(db, session, "party_advance", row.student_id)
    db.commit()
    return party(row)


@router.get("/workbench/party/timeline")
def get_timeline(session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"stages": FLOW_STAGES, "rules": timeline_rules()}


@router.put("/workbench/party/timeline")
def update_timeline(payload: dict, session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    rules = normalize_timeline_rules(payload.get("rules", []))
    timeline_path().write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "rules": rules}


@router.post("/workbench/party/reminders/refresh")
def refresh_reminders(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    rows = db.query(PartyProgress).all()
    changed = 0
    for row in rows:
        if ensure_timeline_task(row):
            changed += 1
    audit(db, session, "party_reminders_refresh", "party_progress", {"changed": changed})
    db.commit()
    return {"ok": True, "students": len(rows), "changed": changed}


def timeline_path() -> Path:
    path = Path(get_settings().upload_dir).parent / "party_timeline.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def timeline_rules() -> list[dict]:
    path = timeline_path()
    if not path.exists():
        return DEFAULT_TIMELINE_RULES
    try:
        return normalize_timeline_rules(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_TIMELINE_RULES


def normalize_timeline_rules(rules: list[dict]) -> list[dict]:
    by_key = {item.get("stageKey"): item for item in rules}
    normalized = []
    for default in DEFAULT_TIMELINE_RULES:
        item = by_key.get(default["stageKey"], {})
        normalized.append(
            {
                "stageKey": default["stageKey"],
                "durationDays": max(0, int(item.get("durationDays", default["durationDays"]) or 0)),
                "remindBeforeDays": max(0, int(item.get("remindBeforeDays", default["remindBeforeDays"]) or 0)),
                "material": str(item.get("material", default["material"]) or ""),
            },
        )
    return normalized


def ensure_timeline_task(row: PartyProgress) -> bool:
    rule = next((item for item in timeline_rules() if item["stageKey"] == row.current_key), None)
    if not rule or rule["durationDays"] <= 0:
        return False
    start_at = current_stage_start(row)
    due_at = int((start_at + timedelta(days=rule["durationDays"])).timestamp() * 1000)
    remind_at = int((start_at + timedelta(days=max(0, rule["durationDays"] - rule["remindBeforeDays"]))).timestamp() * 1000)
    task_id = f"timeline_{row.student_id}_{row.current_key}"
    existing = next((task for task in row.tasks or [] if task.get("id") == task_id), None)
    task = {
        "id": task_id,
        "title": f"{stage_name(row.current_key)}阶段材料提醒",
        "body": f"标准时间线约 {rule['durationDays']} 天，请准备：{rule['material']}",
        "dueAt": due_at,
        "remindAt": remind_at,
        "done": bool(existing.get("done")) if existing else False,
        "source": "timeline",
    }
    next_tasks = [task if item.get("id") == task_id else item for item in row.tasks or []]
    if not existing:
        next_tasks = [task, *next_tasks]
    if next_tasks == (row.tasks or []):
        return False
    row.tasks = next_tasks
    return True


def current_stage_start(row: PartyProgress) -> datetime:
    history = [item for item in row.history or [] if item.get("stageKey") == row.current_key and item.get("at")]
    if history:
        at = max(int(item["at"]) for item in history)
        return datetime.fromtimestamp(at / 1000, tz=timezone.utc)
    return row.updated_at or row.created_at or datetime.now(timezone.utc)


def stage_name(key: str) -> str:
    return next((item["name"] for item in FLOW_STAGES if item["key"] == key), key)
