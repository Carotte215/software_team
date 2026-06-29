from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import PartyProgress, PartyStage, PartyTimelineRule, Student, PartyCalendarEvent
from app.services.common import audit, now_ms, uid
from app.services.party_helpers import sync_political_for_party, sync_stage_from_political, validate_party_advance
from app.services.party_materials import (
    attach_step_materials,
    current_quarter_label,
    detach_step_material,
    enrich_party_step,
    ensure_step_upload_allowed,
    submit_thought_report,
)
from app.services.party_bootstrap import refresh_calendar_reminder_tasks, refresh_party_tasks_from_official
from app.services.party_official_data import (
    ASSETS_DIR,
    CALENDAR_HIGHLIGHTS,
    OFFICIAL_ASSETS,
    OFFICIAL_FLOW_STAGES,
    OFFICIAL_META,
    OFFICIAL_STEPS,
    build_official_guide,
)
from app.services.serializers import party

router = APIRouter(tags=["party"])


@router.get("/party/official-docs")
def official_docs(session: CurrentSession = Depends(get_current_session)) -> dict:
    docs = []
    for key, meta in OFFICIAL_ASSETS.items():
        path = ASSETS_DIR / meta["fileName"]
        docs.append(
            {
                "id": meta["id"],
                "key": key,
                "title": meta["title"],
                "description": meta["description"],
                "fileName": meta["fileName"],
                "available": path.exists(),
                "downloadUrl": f"/api/party/official-docs/{meta['id']}/download",
                "previewUrl": f"/api/party/official-docs/{meta['id']}/preview" if meta["fileName"].lower().endswith((".png", ".jpg", ".jpeg", ".pdf")) else "",
            },
        )
    return {"list": docs, "calendarHighlights": CALENDAR_HIGHLIGHTS, "meta": OFFICIAL_META}


@router.get("/party/official-guide")
def official_guide() -> dict:
    return build_official_guide()


@router.get("/party/official-docs/{doc_id}/download")
def download_official_doc(doc_id: str, session: CurrentSession = Depends(get_current_session)) -> FileResponse:
    meta = next((item for item in OFFICIAL_ASSETS.values() if item["id"] == doc_id), None)
    if not meta:
        raise HTTPException(status_code=404, detail="document not found")
    path = ASSETS_DIR / meta["fileName"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="file missing on server")
    return FileResponse(path, media_type=meta["contentType"], filename=meta["fileName"])


@router.get("/party/official-docs/{doc_id}/preview")
def preview_official_doc(doc_id: str, session: CurrentSession = Depends(get_current_session)) -> FileResponse:
    meta = next((item for item in OFFICIAL_ASSETS.values() if item["id"] == doc_id), None)
    if not meta or not meta["fileName"].lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
        raise HTTPException(status_code=415, detail="preview not supported")
    path = ASSETS_DIR / meta["fileName"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="file missing on server")
    return FileResponse(path, media_type=meta["contentType"], filename=meta["fileName"])


@router.get("/party/calendar-events")
def calendar_events(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    hint_by_date = {item["date"]: item.get("partyHint", "") for item in CALENDAR_HIGHLIGHTS}
    rows = db.scalars(
        select(PartyCalendarEvent).where(PartyCalendarEvent.online.is_(True)).order_by(PartyCalendarEvent.event_date),
    ).all()
    if rows:
        return {
            "list": [
                {
                    "id": row.id,
                    "date": row.event_date,
                    "title": row.title,
                    "note": row.note,
                    "partyHint": hint_by_date.get(row.event_date, ""),
                    "tags": row.tags or [],
                }
                for row in rows
            ],
        }
    return {
        "list": [
            {**item, "partyHint": item.get("partyHint", ""), "tags": item.get("tags", ["校历", "党团"])}
            for item in CALENDAR_HIGHLIGHTS
        ],
    }


@router.get("/workbench/party/calendar")
def list_calendar_admin(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    rows = db.scalars(select(PartyCalendarEvent).order_by(PartyCalendarEvent.event_date)).all()
    return {
        "list": [
            {
                "id": row.id,
                "date": row.event_date,
                "title": row.title,
                "note": row.note,
                "tags": row.tags or [],
                "online": row.online,
            }
            for row in rows
        ],
    }


@router.put("/workbench/party/calendar")
def save_calendar_admin(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    events = payload.get("events") or []
    saved = []
    for item in events:
        event_id = str(item.get("id") or uid("cal")).strip()
        row = db.get(PartyCalendarEvent, event_id) or PartyCalendarEvent(id=event_id)
        row.event_date = str(item.get("date", "")).strip()
        row.title = str(item.get("title", "")).strip()
        row.note = str(item.get("note", "")).strip()
        row.tags = list(item.get("tags") or [])
        row.online = item.get("online", True) is not False
        if not row.title or not row.event_date:
            continue
        db.add(row)
        saved.append(row)
    audit(db, session, "party_calendar_update", "party_calendar_events", {"count": len(saved)})
    db.commit()
    return {"ok": True, "count": len(saved)}


@router.get("/party/progress")
def progress(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    if refresh_party_tasks_from_official(row, db):
        db.commit()
    student = db.get(Student, session.student_id)
    if student and sync_stage_from_political(student, row):
        db.commit()
    stages = load_party_stages(db)
    current_order = next((s["order"] for s in stages if s["key"] == row.current_key), 0)
    completed = set(row.completed_steps or [])
    verified = set(row.verified_steps or [])
    return {
        "flowName": "入党流程",
        "reference": f"依据{OFFICIAL_META['legalBasis']}及学院组织工作常用流程（{OFFICIAL_META['flowSummary']}）",
        "officialMeta": OFFICIAL_META,
        "stages": stages,
        "timelineRules": timeline_rules(db),
        "steps": build_steps_view(row, stages, current_order, completed, verified, row.step_materials or {}),
        "officialDocs": official_doc_refs(),
        "thoughtReports": row.thought_reports or [],
        "currentQuarter": current_quarter_label(),
        **party(row),
    }


@router.post("/party/steps/{step_id}/done")
def complete_step(step_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    valid_ids = {step["id"] for step in OFFICIAL_STEPS}
    if step_id not in valid_ids:
        raise HTTPException(status_code=404, detail="step not found")
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    ensure_step_upload_allowed(row, step_id)
    completed = list(row.completed_steps or [])
    if step_id not in completed:
        completed.append(step_id)
        row.completed_steps = completed
    row.tasks = [
        {**task, "done": True} if task.get("stepId") == step_id or task.get("id") == f"official_{step_id}" else task
        for task in row.tasks or []
    ]
    audit(db, session, "party_step_done", step_id)
    db.commit()
    return {"ok": True, "completedSteps": row.completed_steps}


@router.post("/party/steps/{step_id}/materials")
def attach_party_step_materials(
    step_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    result = attach_step_materials(row, step_id, payload.get("attachments") or [])
    audit(db, session, "party_step_material", f"{step_id}:{len(result['materials'])}")
    db.commit()
    return result


@router.delete("/party/steps/{step_id}/materials/{file_id}")
def remove_party_step_material(
    step_id: str,
    file_id: str,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    from app.services.file_storage import cleanup_orphan_files

    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    result = detach_step_material(row, step_id, file_id)
    audit(db, session, "party_step_material_remove", f"{step_id}:{file_id}")
    db.commit()
    cleanup_orphan_files(db, {file_id})
    return result


@router.get("/party/thought-reports")
def list_thought_reports(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    return {"list": row.thought_reports or [], "currentQuarter": current_quarter_label()}


@router.post("/party/thought-reports")
def create_thought_report(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    entry = submit_thought_report(row, payload)
    audit(db, session, "party_thought_report", entry["id"])
    db.commit()
    return {"ok": True, "report": entry}


@router.post("/workbench/party/steps/verify")
def verify_party_step(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role != "teacher":
        raise HTTPException(status_code=403, detail="forbidden")
    step_id = str(payload.get("stepId", "")).strip()
    student_id = str(payload.get("studentId", "")).strip()
    if step_id not in {step["id"] for step in OFFICIAL_STEPS}:
        raise HTTPException(status_code=404, detail="step not found")
    row = db.get(PartyProgress, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    completed = list(row.completed_steps or [])
    verified = list(row.verified_steps or [])
    if step_id not in completed:
        completed.append(step_id)
    if step_id not in verified:
        verified.append(step_id)
    row.completed_steps = completed
    row.verified_steps = verified
    audit(db, session, "party_step_verify", f"{student_id}:{step_id}")
    db.commit()
    return {"ok": True, "verifiedSteps": row.verified_steps}


@router.get("/workbench/party/students/{student_id}")
def get_student_party_detail(student_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    row = db.get(PartyProgress, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
    stages = load_party_stages(db)
    current_order = next((s["order"] for s in stages if s["key"] == row.current_key), 0)
    completed = set(row.completed_steps or [])
    verified = set(row.verified_steps or [])
    return {
        "studentId": student_id,
        "steps": [s for s in build_steps_view(row, stages, current_order, completed, verified, row.step_materials or {}) if s.get("pendingVerify")],
        "thoughtReports": row.thought_reports or [],
        "stepMaterials": row.step_materials or {},
    }


@router.get("/workbench/party/export")
def export_party_progress(
    class_name: str = "",
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
):
    import csv
    from io import StringIO
    from urllib.parse import quote

    from fastapi.responses import Response

    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    students = {row.student_id: row for row in db.scalars(select(Student)).all()}
    stages = {item["key"]: item["name"] for item in load_party_stages(db)}
    fp = StringIO()
    writer = csv.writer(fp)
    writer.writerow(["学号", "姓名", "班级", "年级", "当前阶段", "已自勾环节", "已确认环节", "材料文件数", "思想汇报数", "待办数"])
    for row in db.scalars(select(PartyProgress).order_by(PartyProgress.student_id)).all():
        student = students.get(row.student_id)
        if class_name and (not student or student.class_name != class_name):
            continue
        pending = len([task for task in row.tasks or [] if not task.get("done")])
        material_count = sum(len(items or []) for items in (row.step_materials or {}).values())
        writer.writerow([
            row.student_id,
            student.name if student else "",
            student.class_name if student else "",
            student.grade if student else "",
            stages.get(row.current_key, row.current_key),
            len(row.completed_steps or []),
            len(row.verified_steps or []),
            material_count,
            len(row.thought_reports or []),
            pending,
        ])
    filename = quote("党团进度台账.csv")
    return Response(
        "\ufeff" + fp.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/workbench/party/progress")
def list_party_progress(
    class_name: str = "",
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    if session.role not in {"teacher", "leader"}:
        raise HTTPException(status_code=403, detail="forbidden")
    students = {row.student_id: row for row in db.scalars(select(Student)).all()}
    stages = {item["key"]: item["name"] for item in load_party_stages(db)}
    payload = []
    for row in db.scalars(select(PartyProgress).order_by(PartyProgress.updated_at.desc())).all():
        student = students.get(row.student_id)
        if class_name and (not student or student.class_name != class_name):
            continue
        total_steps = len([s for s in OFFICIAL_STEPS if s["stageKey"] == row.current_key])
        done_steps = len([s for s in row.verified_steps or [] if any(step["id"] == s and step["stageKey"] == row.current_key for step in OFFICIAL_STEPS)])
        material_count = sum(len(items or []) for items in (row.step_materials or {}).values())
        payload.append(
            {
                **party(row),
                "name": student.name if student else "",
                "className": student.class_name if student else "",
                "grade": student.grade if student else "",
                "currentStageName": stages.get(row.current_key, row.current_key),
                "stepProgress": f"{done_steps}/{total_steps}" if total_steps else "—",
                "materialCount": material_count,
                "thoughtReportCount": len(row.thought_reports or []),
            },
        )
    return {"list": payload, "stages": load_party_stages(db)}


@router.post("/party/tasks/{task_id}/done")
def complete_task(task_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(PartyProgress, session.student_id)
    if not row:
        raise HTTPException(status_code=404, detail="party progress not found")
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
    next_key = str(payload.get("nextKey", "")).strip()
    force = bool(payload.get("force"))
    validate_party_advance(row, next_key, force=force)
    row.current_key = next_key
    row.history = [*row.history, {"stageKey": next_key, "at": now_ms(), "remark": payload.get("remark", "管理端推进阶段")}]
    student = db.get(Student, row.student_id)
    if student:
        sync_political_for_party(student, next_key)
    refresh_party_tasks_from_official(row, db)
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
        if (
            ensure_timeline_task(row)
            or refresh_party_tasks_from_official(row, db)
            or refresh_calendar_reminder_tasks(row, db)
        ):
            changed += 1
    audit(db, session, "party_reminders_refresh", "party_progress", {"changed": changed})
    db.commit()
    return {"ok": True, "students": len(rows), "changed": changed}


def build_steps_view(
    row: PartyProgress,
    stages: list[dict],
    current_order: int,
    completed: set[str],
    verified: set[str],
    step_materials: dict | None = None,
) -> list[dict]:
    result = []
    for step in OFFICIAL_STEPS:
        stage = next((s for s in stages if s["key"] == step["stageKey"]), None)
        stage_order = stage["order"] if stage else 0
        auto_done = stage_order < current_order
        self_done = step["id"] in completed or auto_done
        is_verified = step["id"] in verified or auto_done
        base = enrich_party_step(step, step_materials)
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


def official_doc_refs() -> list[dict]:
    return [
        {"id": meta["id"], "title": meta["title"], "downloadUrl": f"/api/party/official-docs/{meta['id']}/download"}
        for meta in OFFICIAL_ASSETS.values()
    ]


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
    for item in OFFICIAL_FLOW_STAGES:
        db.merge(
            PartyTimelineRule(
                stage_key=item["key"],
                duration_days=item["durationDays"],
                remind_before_days=item["remindBeforeDays"],
                material=item["material"],
            ),
        )
    db.commit()
    return [
        {
            "stageKey": item["key"],
            "durationDays": item["durationDays"],
            "remindBeforeDays": item["remindBeforeDays"],
            "material": item["material"],
        }
        for item in OFFICIAL_FLOW_STAGES
    ]


def normalize_timeline_rules(rules: list[dict]) -> list[dict]:
    defaults = {item["key"]: item for item in OFFICIAL_FLOW_STAGES}
    by_key = {item.get("stageKey"): item for item in rules}
    normalized = []
    for key, default in defaults.items():
        item = by_key.get(key, {})
        normalized.append(
            {
                "stageKey": key,
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
    stage = stage_name(row.current_key, db)
    task = {
        "id": task_id,
        "title": f"{stage}阶段材料提醒",
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
    for item in OFFICIAL_FLOW_STAGES:
        db.merge(PartyStage(stage_key=item["key"], name=item["name"], desc=item["desc"], sort_order=item["order"]))
    db.commit()
    return [{"key": i["key"], "name": i["name"], "desc": i["desc"], "order": i["order"]} for i in OFFICIAL_FLOW_STAGES]


def stage_name(key: str, db: Session | None = None) -> str:
    if db is not None:
        row = db.get(PartyStage, key)
        if row:
            return row.name
    return next((item["name"] for item in OFFICIAL_FLOW_STAGES if item["key"] == key), key)
