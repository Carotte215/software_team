"""将党团官方文件与结构化内容写入数据库与文件存储（支持已有库增量更新）。"""

import json
import shutil
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApplicationTemplate, KnowledgeItem, LeagueProgress, LeagueTimelineRule, PartyCalendarEvent, PartyProgress, PartyStage, PartyTimelineRule, Student, TemplateFile, TheoryQuestion
from app.services.seed_data import APPLICATION_TEMPLATES, KNOWLEDGE_BODIES, THEORY_QUESTIONS
from app.services.file_storage import data_path, meta_path, storage_root
from app.services.party_official_data import (
    ASSETS_DIR,
    CALENDAR_HIGHLIGHTS,
    LEAGUE_TIMELINE,
    OFFICIAL_ASSETS,
    OFFICIAL_FLOW_STAGES,
    OFFICIAL_KNOWLEDGE,
    OFFICIAL_TEMPLATES,
    OFFICIAL_THEORY_QUESTIONS,
)


def ensure_party_official_content(db: Session) -> None:
    asset_files = register_official_assets()
    upsert_party_stages(db)
    upsert_timeline_rules(db)
    upsert_knowledge(db, asset_files)
    upsert_seed_knowledge(db)
    upsert_templates(db, asset_files)
    upsert_thought_report_template(db)
    upsert_theory_questions(db)
    upsert_application_templates(db)
    upsert_league_timeline(db)
    upsert_calendar_events(db)
    ensure_league_progress(db)
    db.commit()


def register_official_assets() -> dict[str, str]:
    """复制 assets/party 到 uploads，返回 asset_key -> file_id。"""
    storage_root()
    mapping: dict[str, str] = {}
    for key, meta in OFFICIAL_ASSETS.items():
        file_id = f"asset_{meta['id']}"
        source = ASSETS_DIR / meta["fileName"]
        if not source.exists():
            continue
        suffix = source.suffix.lower()
        target = data_path(file_id, suffix)
        if not target.exists() or target.stat().st_size != source.stat().st_size:
            shutil.copy2(source, target)
        meta_payload = {
            "id": file_id,
            "name": meta["fileName"],
            "size": target.stat().st_size,
            "contentType": meta["contentType"],
            "business": "template",
            "suffix": suffix,
            "url": f"/api/files/{file_id}/download",
            "uploadedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
            "uploadedBy": "system",
        }
        meta_path(file_id).write_text(json.dumps(meta_payload, ensure_ascii=False), encoding="utf-8")
        mapping[key] = file_id
    return mapping


def attachment_payload(asset_key: str, asset_files: dict[str, str]) -> dict | None:
    from pathlib import Path

    meta = OFFICIAL_ASSETS.get(asset_key)
    file_id = asset_files.get(asset_key)
    if not meta or not file_id:
        return None
    suffix = Path(meta["fileName"]).suffix
    return {
        "id": file_id,
        "name": meta["title"] + suffix,
        "url": f"/api/files/{file_id}/download",
        "previewUrl": f"/api/files/{file_id}/preview" if meta["fileName"].lower().endswith((".png", ".jpg", ".jpeg", ".pdf")) else "",
    }


def upsert_party_stages(db: Session) -> None:
    for item in OFFICIAL_FLOW_STAGES:
        db.merge(
            PartyStage(
                stage_key=item["key"],
                name=item["name"],
                desc=item["desc"],
                sort_order=item["order"],
            ),
        )


def upsert_timeline_rules(db: Session) -> None:
    for item in OFFICIAL_FLOW_STAGES:
        db.merge(
            PartyTimelineRule(
                stage_key=item["key"],
                duration_days=item["durationDays"],
                remind_before_days=item["remindBeforeDays"],
                material=item["material"],
            ),
        )


def upsert_knowledge(db: Session, asset_files: dict[str, str]) -> None:
    for kid, title, category, tags, summary, body, sensitive, asset_keys in OFFICIAL_KNOWLEDGE:
        attachments = [payload for key in asset_keys if (payload := attachment_payload(key, asset_files))]
        existing = db.get(KnowledgeItem, kid)
        row = existing or KnowledgeItem(id=kid)
        row.title = title
        row.category = category
        row.tags = tags
        row.summary = summary
        row.body = body
        row.sensitive_hint = sensitive
        row.online = True
        if attachments:
            row.attachments = attachments
        db.add(row)


def upsert_templates(db: Session, asset_files: dict[str, str]) -> None:
    for tid, name, scene, fmt, asset_key in OFFICIAL_TEMPLATES:
        file_id = asset_files.get(asset_key or "") if asset_key else ""
        existing = db.get(TemplateFile, tid)
        row = existing or TemplateFile(id=tid)
        row.name = name
        row.scene = scene
        row.format = fmt
        if file_id:
            row.file_id = file_id
            row.file_url = f"/api/templates/{tid}/download"
        db.add(row)


def upsert_seed_knowledge(db: Session) -> None:
    """将种子知识库条目从占位正文升级为可用说明（不覆盖官方条目）。"""
    for kid, body in KNOWLEDGE_BODIES.items():
        row = db.get(KnowledgeItem, kid)
        if not row:
            continue
        placeholder = "请以学院官网最新通知为准"
        if placeholder in (row.body or "") or len((row.body or "").strip()) < 80:
            row.body = body
            db.add(row)


def upsert_thought_report_template(db: Session) -> None:
    """为思想汇报模板生成可下载 HTML 文件。"""
    from app.services.seed_data import THOUGHT_REPORT_HTML

    file_id = "asset_tpl_report"
    target = data_path(file_id, ".html")
    content = THOUGHT_REPORT_HTML.encode("utf-8")
    if not target.exists() or target.read_bytes() != content:
        target.write_bytes(content)
    meta_path(file_id).write_text(
        json.dumps(
            {
                "id": file_id,
                "name": "思想汇报模板.html",
                "size": len(content),
                "contentType": "text/html",
                "business": "template",
                "suffix": ".html",
                "url": f"/api/files/{file_id}/download",
                "uploadedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
                "uploadedBy": "system",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    row = db.get(TemplateFile, "tpl_report")
    if row:
        row.file_id = file_id
        row.file_url = "/api/templates/tpl_report/download"
        row.format = "html"
        db.add(row)


def upsert_theory_questions(db: Session) -> None:
    merged: dict[str, tuple] = {}
    for qid, stem, opts, ans, expl, cat in THEORY_QUESTIONS:
        merged[qid] = (qid, stem, opts, ans, expl, cat)
    for qid, stem, opts, ans, expl, cat in OFFICIAL_THEORY_QUESTIONS:
        merged[qid] = (qid, stem, opts, ans, expl, cat)
    for qid, stem, opts, ans, expl, cat in merged.values():
        existing = db.get(TheoryQuestion, qid)
        row = existing or TheoryQuestion(id=qid)
        row.stem = stem
        row.options = [o for o in opts.split(";") if o]
        row.answer = ans
        row.explanation = expl
        row.category = cat
        row.online = True
        db.add(row)


def upsert_calendar_events(db: Session) -> None:
    from app.services.party_official_data import CALENDAR_HIGHLIGHTS

    for item in CALENDAR_HIGHLIGHTS:
        event_id = f"cal_{item['date'].replace('-', '')}"
        row = db.get(PartyCalendarEvent, event_id) or PartyCalendarEvent(id=event_id)
        row.event_date = item["date"]
        row.title = item["title"]
        note = item.get("note", "")
        if item.get("partyHint"):
            note = f"{note}｜党团提示：{item['partyHint']}" if note else f"党团提示：{item['partyHint']}"
        row.note = note
        row.tags = list(item.get("tags") or ["校历", "党团"])
        row.online = True
        db.add(row)


def ensure_league_progress(db: Session) -> None:
    existing = {row.student_id for row in db.scalars(select(LeagueProgress)).all()}
    defaults = {
        "共青团员": "l_member",
        "入团积极分子": "l_activist",
        "中共预备党员": "l_member",
        "入党积极分子": "l_apply",
    }
    for student in db.scalars(select(Student)).all():
        if student.student_id in existing:
            continue
        political = (student.political_status or "").strip()
        current = defaults.get(political, "l_apply")
        db.add(
            LeagueProgress(
                student_id=student.student_id,
                current_key=current,
                history=[{"stageKey": "l_apply", "at": int(datetime.now(timezone.utc).timestamp() * 1000), "remark": "系统初始化"}],
                tasks=[],
                completed_steps=[],
            ),
        )


def refresh_league_tasks_from_official(row: LeagueProgress, db: Session) -> bool:
    from app.services.party_official_data import LEAGUE_STEPS

    changed = False
    tasks = list(row.tasks or [])
    existing_ids = {task.get("id") for task in tasks}
    stage_steps = [step for step in LEAGUE_STEPS if step["stageKey"] == row.current_key]
    for step in stage_steps[:2]:
        task_id = f"official_{step['id']}"
        if task_id in existing_ids:
            continue
        tasks.append(
            {
                "id": task_id,
                "title": f"【官方环节】{step['name']}",
                "body": step["detail"],
                "dueAt": None,
                "done": False,
                "source": "official_step",
                "stepId": step["id"],
            },
        )
        changed = True
    if changed:
        row.tasks = tasks
    return changed


def upsert_application_templates(db: Session) -> None:
    for tid, name, apply_type, subtype, body_html in APPLICATION_TEMPLATES:
        existing = db.get(ApplicationTemplate, tid)
        row = existing or ApplicationTemplate(id=tid)
        row.name = name
        row.apply_type = apply_type
        row.subtype = subtype
        row.body_html = body_html
        db.add(row)


def upsert_league_timeline(db: Session) -> None:
    for item in LEAGUE_TIMELINE:
        db.merge(
            LeagueTimelineRule(
                stage_key=item["stageKey"],
                duration_days=item["durationDays"],
                remind_before_days=item["remindBeforeDays"],
                material=item["material"],
            ),
        )


def refresh_party_tasks_from_official(row: PartyProgress, db: Session) -> bool:
    """为当前阶段补充官方环节待办（不覆盖已有自定义任务）。"""
    from app.services.party_official_data import OFFICIAL_STEPS

    changed = False
    tasks = list(row.tasks or [])
    existing_ids = {task.get("id") for task in tasks}
    stage_steps = [step for step in OFFICIAL_STEPS if step["stageKey"] == row.current_key]
    for step in stage_steps[:3]:
        task_id = f"official_{step['id']}"
        if task_id in existing_ids:
            continue
        tasks.append(
            {
                "id": task_id,
                "title": f"【官方环节】{step['name']}",
                "body": step["detail"],
                "dueAt": None,
                "done": False,
                "source": "official_step",
                "stepId": step["id"],
            },
        )
        changed = True
    if changed:
        row.tasks = tasks
    return changed


def _upcoming_calendar_events(db: Session) -> list[dict]:
    hint_by_date = {item["date"]: item.get("partyHint", "") for item in CALENDAR_HIGHLIGHTS}
    rows = db.scalars(
        select(PartyCalendarEvent).where(PartyCalendarEvent.online.is_(True)).order_by(PartyCalendarEvent.event_date),
    ).all()
    if rows:
        return [
            {
                "date": row.event_date,
                "title": row.title,
                "note": row.note or "",
                "partyHint": hint_by_date.get(row.event_date, ""),
            }
            for row in rows
        ]
    return list(CALENDAR_HIGHLIGHTS)


def refresh_calendar_reminder_tasks(row: PartyProgress, db: Session, horizon_days: int = 21) -> bool:
    """根据校历要点为近 horizon_days 内的节点生成待办（FR2 / Phase 3 校历联动）。"""
    if row.current_key in {"apply", ""}:
        return False
    today = date.today()
    horizon = today + timedelta(days=horizon_days)
    changed = False
    tasks = list(row.tasks or [])
    existing_ids = {task.get("id") for task in tasks}
    for event in _upcoming_calendar_events(db):
        raw_date = str(event.get("date", ""))[:10]
        try:
            event_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if not (today <= event_date <= horizon):
            continue
        task_id = f"calendar_{raw_date}"
        if task_id in existing_ids:
            continue
        title = str(event.get("title", "校历节点"))
        note = str(event.get("note", "")).strip()
        party_hint = str(event.get("partyHint", "")).strip()
        if party_hint:
            note = f"{note} 党团提示：{party_hint}".strip()
        if "考试" in title:
            note = f"{note} 请提前准备思想汇报与组织生活材料。".strip()
        due_at = int(datetime(event_date.year, event_date.month, event_date.day, tzinfo=timezone.utc).timestamp() * 1000)
        tasks.append(
            {
                "id": task_id,
                "title": f"【校历】{title}",
                "body": note or f"请关注 {raw_date} 校历安排。",
                "dueAt": due_at,
                "done": False,
                "source": "calendar",
            },
        )
        changed = True
    if changed:
        row.tasks = tasks
    return changed
