from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import PartyProgress, PartyStage, PartyTimelineRule, Student
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
    return {"flowName": "入党流程", "stages": load_party_stages(db), "timelineRules": timeline_rules(db), **party(row)}


@router.get("/workbench/party/progress")
def list_party_progress(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    students = {row.student_id: row for row in db.scalars(select(Student)).all()}
    stages = {item["key"]: item["name"] for item in load_party_stages(db)}
    payload = []
    for row in db.scalars(select(PartyProgress).order_by(PartyProgress.updated_at.desc())).all():
        student = students.get(row.student_id)
        payload.append(
            {
                **party(row),
                "name": student.name if student else "",
                "className": student.class_name if student else "",
                "grade": student.grade if student else "",
                "currentStageName": stages.get(row.current_key, row.current_key),
            },
        )
    return {"list": payload, "stages": load_party_stages(db)}


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


@router.put("/workbench/party/stages")
def update_party_stages(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    stages = payload.get("stages", [])
    for item in stages:
        db.merge(
            PartyStage(
                stage_key=item.get("key") or item.get("stageKey"),
                name=item.get("name", ""),
                desc=item.get("desc", ""),
                sort_order=int(item.get("order") or item.get("sortOrder") or 0),
            ),
        )
    audit(db, session, "party_stages_update", "party_stages", {"count": len(stages)})
    db.commit()
    return {"ok": True, "stages": load_party_stages(db)}


@router.get("/workbench/party/timeline")
def get_timeline(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"stages": load_party_stages(db), "rules": timeline_rules(db)}


@router.put("/workbench/party/timeline")
def update_timeline(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    rules = normalize_timeline_rules(payload.get("rules", []))
    for item in rules:
        db.merge(
            PartyTimelineRule(
                stage_key=item["stageKey"],
                duration_days=item["durationDays"],
                remind_before_days=item["remindBeforeDays"],
                material=item["material"],
            ),
        )
    audit(db, session, "party_timeline_update", "party_timeline_rules", {"count": len(rules)})
    db.commit()
    return {"ok": True, "rules": rules}


@router.post("/workbench/party/reminders/refresh")
def refresh_reminders(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    return run_party_reminders(db, session)


def run_party_reminders(db: Session, session: CurrentSession) -> dict:
    rows = db.query(PartyProgress).all()
    changed = 0
    for row in rows:
        if ensure_timeline_task(row):
            changed += 1
    audit(db, session, "party_reminders_refresh", "party_progress", {"changed": changed})
    return {"ok": True, "students": len(rows), "changed": changed}


def timeline_rules(db: Session) -> list[dict]:
    rows = db.scalars(select(PartyTimelineRule)).all()
    if rows:
        return normalize_timeline_rules(
            [
                {
                    "stageKey": row.stage_key,
                    "durationDays": row.duration_days,
                    "remindBeforeDays": row.remind_before_days,
                    "material": row.material,
                }
                for row in rows
            ],
        )
    for item in DEFAULT_TIMELINE_RULES:
        db.merge(
            PartyTimelineRule(
                stage_key=item["stageKey"],
                duration_days=item["durationDays"],
                remind_before_days=item["remindBeforeDays"],
                material=item["material"],
            ),
        )
    db.commit()
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
    db = Session.object_session(row)
    rule = next((item for item in timeline_rules(db) if item["stageKey"] == row.current_key), None) if db else None
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


def load_party_stages(db: Session) -> list[dict]:
    rows = db.scalars(select(PartyStage).order_by(PartyStage.sort_order)).all()
    if rows:
        return [{"key": r.stage_key, "name": r.name, "desc": r.desc, "order": r.sort_order} for r in rows]
    for item in FLOW_STAGES:
        db.merge(PartyStage(stage_key=item["key"], name=item["name"], desc=item["desc"], sort_order=item["order"]))
    db.commit()
    return FLOW_STAGES


def stage_name(key: str, db: Session | None = None) -> str:
    if db is not None:
        row = db.get(PartyStage, key)
        if row:
            return row.name
    return next((item["name"] for item in FLOW_STAGES if item["key"] == key), key)
