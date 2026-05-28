from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import LeagueProgress, LeagueTimelineRule, Student
from app.services.common import audit, now_ms
from app.services.party_materials import (
    attach_step_materials,
    detach_step_material,
    enrich_league_step,
    ensure_step_upload_allowed,
)
from app.services.party_helpers import sync_political_for_league, validate_league_advance
from app.services.party_bootstrap import refresh_league_tasks_from_official
from app.services.party_official_data import LEAGUE_FLOW_STAGES, LEAGUE_STEPS, LEAGUE_TIMELINE, OFFICIAL_ASSETS, OFFICIAL_META
from app.services.serializers import league

router = APIRouter(tags=["league"])


@router.get("/league/progress")
def progress(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(LeagueProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    if refresh_league_tasks_from_official(row, db):
        db.commit()
    stages = load_league_stages()
    current_order = next((s["order"] for s in stages if s["key"] == row.current_key), 0)
    completed = set(row.completed_steps or [])
    verified = set(row.verified_steps or [])
    return {
        "flowName": "入团流程",
        "reference": f"依据{OFFICIAL_META['leagueBasis']}（{OFFICIAL_META['leagueFlowSummary']}）",
        "officialMeta": OFFICIAL_META,
        "stages": stages,
        "timelineRules": league_timeline_rules(db),
        "steps": build_steps_view(row, stages, current_order, completed, verified, row.step_materials or {}),
        "officialDocs": [
            {"id": meta["id"], "title": meta["title"], "downloadUrl": f"/api/party/official-docs/{meta['id']}/download"}
            for key, meta in OFFICIAL_ASSETS.items()
            if key in {"league_cert", "calendar"}
        ],
        **league(row),
    }


@router.post("/league/steps/{step_id}/done")
def complete_step(step_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if step_id not in {step["id"] for step in LEAGUE_STEPS}:
        raise HTTPException(status_code=404, detail="step not found")
    row = db.get(LeagueProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    ensure_step_upload_allowed(row, step_id, league=True)
    completed = list(row.completed_steps or [])
    if step_id not in completed:
        completed.append(step_id)
        row.completed_steps = completed
    row.tasks = [
        {**task, "done": True} if task.get("stepId") == step_id or task.get("id") == f"official_{step_id}" else task
        for task in row.tasks or []
    ]
    audit(db, session, "league_step_done", step_id)
    db.commit()
    return {"ok": True, "completedSteps": row.completed_steps}


@router.post("/league/tasks/{task_id}/done")
def complete_task(task_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(LeagueProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    step_id = None
    for task in row.tasks or []:
        if task.get("id") == task_id:
            step_id = task.get("stepId")
            break
    row.tasks = [{**task, "done": True} if task.get("id") == task_id else task for task in row.tasks]
    if step_id:
        completed = list(row.completed_steps or [])
        if step_id not in completed:
            completed.append(step_id)
            row.completed_steps = completed
    audit(db, session, "league_task_done", task_id)
    db.commit()
    return {"ok": True}


@router.post("/league/steps/{step_id}/materials")
def attach_league_step_materials(
    step_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    row = db.get(LeagueProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    result = attach_step_materials(row, step_id, payload.get("attachments") or [], league=True)
    audit(db, session, "league_step_material", f"{step_id}:{len(result['materials'])}")
    db.commit()
    return result


@router.delete("/league/steps/{step_id}/materials/{file_id}")
def remove_league_step_material(
    step_id: str,
    file_id: str,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    from app.services.file_storage import cleanup_orphan_files

    row = db.get(LeagueProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    result = detach_step_material(row, step_id, file_id)
    audit(db, session, "league_step_material_remove", f"{step_id}:{file_id}")
    db.commit()
    cleanup_orphan_files(db, {file_id})
    return result


@router.get("/workbench/league/students/{student_id}")
def get_student_league_detail(student_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    row = db.get(LeagueProgress, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    stages = load_league_stages()
    current_order = next((s["order"] for s in stages if s["key"] == row.current_key), 0)
    completed = set(row.completed_steps or [])
    verified = set(row.verified_steps or [])
    return {
        "studentId": student_id,
        "steps": [s for s in build_steps_view(row, stages, current_order, completed, verified, row.step_materials or {}) if s.get("pendingVerify")],
        "stepMaterials": row.step_materials or {},
    }


@router.post("/workbench/league/steps/verify")
def verify_league_step(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    step_id = str(payload.get("stepId", "")).strip()
    student_id = str(payload.get("studentId", "")).strip()
    if step_id not in {step["id"] for step in LEAGUE_STEPS}:
        raise HTTPException(status_code=404, detail="step not found")
    row = db.get(LeagueProgress, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    completed = list(row.completed_steps or [])
    verified = list(row.verified_steps or [])
    if step_id not in completed:
        completed.append(step_id)
    if step_id not in verified:
        verified.append(step_id)
    row.completed_steps = completed
    row.verified_steps = verified
    audit(db, session, "league_step_verify", f"{student_id}:{step_id}")
    db.commit()
    return {"ok": True, "verifiedSteps": row.verified_steps}


@router.get("/workbench/league/progress")
def list_league_progress(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    students = {row.student_id: row for row in db.scalars(select(Student)).all()}
    stages = {item["key"]: item["name"] for item in load_league_stages()}
    payload = []
    for row in db.scalars(select(LeagueProgress).order_by(LeagueProgress.updated_at.desc())).all():
        student = students.get(row.student_id)
        total_steps = len([s for s in LEAGUE_STEPS if s["stageKey"] == row.current_key])
        done_steps = len([s for s in row.verified_steps or [] if any(step["id"] == s and step["stageKey"] == row.current_key for step in LEAGUE_STEPS)])
        payload.append(
            {
                **league(row),
                "name": student.name if student else "",
                "className": student.class_name if student else "",
                "grade": student.grade if student else "",
                "currentStageName": stages.get(row.current_key, row.current_key),
                "stepProgress": f"{done_steps}/{total_steps}" if total_steps else "—",
            },
        )
    return {"list": payload, "stages": load_league_stages(), "rules": league_timeline_rules(db)}


@router.post("/workbench/league/advance")
def advance(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    row = db.get(LeagueProgress, payload.get("studentId"))
    if not row:
        raise HTTPException(status_code=404, detail="league progress not found")
    next_key = str(payload.get("nextKey", "")).strip()
    force = bool(payload.get("force"))
    validate_league_advance(row, next_key, force=force)
    row.current_key = next_key
    row.history = [*row.history, {"stageKey": next_key, "at": now_ms(), "remark": payload.get("remark", "管理端推进入团阶段")}]
    student = db.get(Student, row.student_id)
    if student:
        sync_political_for_league(student, next_key)
    refresh_league_tasks_from_official(row, db)
    ensure_league_timeline_task(row, db)
    audit(db, session, "league_advance", row.student_id)
    db.commit()
    return league(row)


@router.post("/workbench/league/reminders/refresh")
def refresh_league_reminders(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    result = run_league_reminders(db, session)
    db.commit()
    return result


def run_league_reminders(db: Session, session: CurrentSession) -> dict:
    changed = 0
    for row in db.scalars(select(LeagueProgress)).all():
        if ensure_league_timeline_task(row, db) or refresh_league_tasks_from_official(row, db):
            changed += 1
    audit(db, session, "league_reminders_refresh", "league_progress", {"changed": changed})
    return {"ok": True, "changed": changed}


def build_steps_view(
    row: LeagueProgress,
    stages: list[dict],
    current_order: int,
    completed: set[str],
    verified: set[str],
    step_materials: dict | None = None,
) -> list[dict]:
    result = []
    for step in LEAGUE_STEPS:
        stage = next((s for s in stages if s["key"] == step["stageKey"]), None)
        stage_order = stage["order"] if stage else 0
        auto_done = stage_order < current_order
        self_done = step["id"] in completed or auto_done
        is_verified = step["id"] in verified or auto_done
        base = enrich_league_step(step, step_materials)
        result.append(
            {
                **base,
                "selfDone": self_done,
                "verified": is_verified,
                "pendingVerify": self_done and not is_verified and not auto_done,
                "done": is_verified,
                "current": step["stageKey"] == row.current_key,
                "upcoming": stage_order > current_order,
                "passed": auto_done,
            },
        )
    return result


def load_league_stages() -> list[dict]:
    return LEAGUE_FLOW_STAGES


def league_timeline_rules(db: Session) -> list[dict]:
    rows = db.scalars(select(LeagueTimelineRule)).all()
    if rows:
        return [
            {
                "stageKey": row.stage_key,
                "durationDays": row.duration_days,
                "remindBeforeDays": row.remind_before_days,
                "material": row.material,
            }
            for row in rows
        ]
    for item in LEAGUE_TIMELINE:
        db.merge(
            LeagueTimelineRule(
                stage_key=item["stageKey"],
                duration_days=item["durationDays"],
                remind_before_days=item["remindBeforeDays"],
                material=item["material"],
            ),
        )
    db.commit()
    return LEAGUE_TIMELINE


def ensure_league_timeline_task(row: LeagueProgress, db: Session) -> bool:
    rule = next((item for item in league_timeline_rules(db) if item["stageKey"] == row.current_key), None)
    if not rule or rule["durationDays"] <= 0:
        return False
    start_at = current_stage_start(row)
    due_at = int((start_at + timedelta(days=rule["durationDays"])).timestamp() * 1000)
    task_id = f"league_timeline_{row.student_id}_{row.current_key}"
    existing = next((task for task in row.tasks or [] if task.get("id") == task_id), None)
    stage = next((s["name"] for s in LEAGUE_FLOW_STAGES if s["key"] == row.current_key), row.current_key)
    task = {
        "id": task_id,
        "title": f"{stage}阶段材料提醒",
        "body": f"标准时间线约 {rule['durationDays']} 天，请准备：{rule['material']}",
        "dueAt": due_at,
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


def current_stage_start(row: LeagueProgress) -> datetime:
    history = [item for item in row.history or [] if item.get("stageKey") == row.current_key and item.get("at")]
    if history:
        at = max(int(item["at"]) for item in history)
        return datetime.fromtimestamp(at / 1000, tz=timezone.utc)
    return row.updated_at or row.created_at or datetime.now(timezone.utc)
