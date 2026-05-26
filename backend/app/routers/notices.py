from datetime import datetime, timezone



from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import func, select

from sqlalchemy.orm import Session



from app.db.session import get_db

from app.deps import CurrentSession, get_current_session

from app.models import Message, Notice, NoticeBatch, Student

from app.schemas import NoticeFetchUrl, NoticeImport, NoticePublish

from app.services.common import audit, uid

from app.services.message_channels import dispatch_notice, empty_scheduled_channels

from app.services.serializers import batch, message, notice



router = APIRouter(tags=["notices"])





@router.get("/notices")

def list_notices(db: Session = Depends(get_db)) -> dict:

    rows = db.scalars(select(Notice).where(Notice.published_at <= datetime.now(timezone.utc)).order_by(Notice.published_at.desc())).all()

    return {"list": [notice(row) for row in rows]}





@router.get("/notices/{notice_id}")

def get_notice(notice_id: str, db: Session = Depends(get_db)) -> dict:

    row = db.get(Notice, notice_id)

    if not row:

        raise HTTPException(status_code=404, detail="notice not found")

    return notice(row)





@router.get("/messages/inbox")

def inbox(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    rows = db.scalars(select(Message).where(Message.student_id == session.student_id).order_by(Message.created_at.desc())).all()

    return {"list": [message(row) for row in rows], "unread": sum(1 for row in rows if not row.read_at)}





@router.post("/messages/{message_id}/read")

def mark_read(message_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    row = db.get(Message, message_id)

    if not row or row.student_id != session.student_id:

        raise HTTPException(status_code=404, detail="message not found")

    row.read_at = datetime.now(timezone.utc)

    db.commit()

    return {"ok": True}





@router.post("/workbench/notices/import")

def import_notice(payload: NoticeImport, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    """FR3-1：管理员录入或导入外部通知。"""

    if session.role not in {"teacher", "coordinator"}:

        raise HTTPException(status_code=403, detail="forbidden")

    row = Notice(

        id=uid("n"),

        title=payload.title,

        tags=payload.tags,

        summary=payload.summary or payload.title,

        content=payload.content or payload.summary,

        source=payload.source,

        published_at=datetime.now(timezone.utc),

    )

    db.add(row)

    audit(db, session, "notice_import", row.id, {"source": payload.source})

    db.commit()

    return notice(row)


@router.post("/workbench/notices/fetch-url")
def fetch_notice_url(payload: NoticeFetchUrl, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    """FR3-2：从 URL 抓取通知正文（简化 HTML 提取）。"""
    import re
    import urllib.request

    if session.role not in {"teacher", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="invalid url")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "StudentServiceBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(512_000).decode("utf-8", errors="ignore")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"fetch failed: {exc}") from exc

    title_m = re.search(r"<title[^>]*>([^<]+)</title>", raw, re.I)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else url
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)<p[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+\n", "\n", re.sub(r"[ \t]+", " ", text)).strip()
    summary = text[:200] + ("…" if len(text) > 200 else "")
    content = text[:8000]

    row = Notice(
        id=uid("n"),
        title=title[:200],
        tags=["外部"],
        summary=summary,
        content=content,
        source=payload.source,
        published_at=datetime.now(timezone.utc),
    )
    db.add(row)
    audit(db, session, "notice_fetch_url", row.id, {"url": url})
    db.commit()
    return notice(row)


@router.post("/workbench/notices/publish")

def publish_notice(payload: NoticePublish, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    if session.role not in {"teacher", "coordinator"}:

        raise HTTPException(status_code=403, detail="forbidden")

    now = datetime.now(timezone.utc)

    scheduled_at = max(0, int(payload.scheduled_at or 0))

    scheduled = scheduled_at > int(now.timestamp() * 1000)

    notice_row = Notice(

        id=uid("n"),

        title=payload.title,

        tags=payload.tags,

        summary=payload.summary or payload.title,

        content=payload.content or payload.summary,

        source=payload.source,

        published_at=datetime.fromtimestamp(scheduled_at / 1000, tz=timezone.utc) if scheduled else now,

    )

    students = db.scalars(select(Student)).all()

    current = db.get(Student, session.student_id)

    targets = [s for s in students if match_rule(payload.target_rule, s, session, current)]

    target_rule = {

        **payload.target_rule,

        "_schedule": {

            "noticeId": notice_row.id,

            "status": "scheduled" if scheduled else "sent",

            "scheduledAt": scheduled_at or int(now.timestamp() * 1000),

            "targetCount": len(targets),

        },

    }

    batch_row = NoticeBatch(

        id=uid("batch"),

        title=payload.title,

        target_rule=target_rule,

        channels=empty_scheduled_channels(len(targets)) if scheduled else [],

    )

    db.add(notice_row)

    db.add(batch_row)

    if not scheduled:

        batch_row.channels = dispatch_notice(db, notice_row, batch_row.id, targets)

    audit(db, session, "notice_schedule" if scheduled else "notice_publish", batch_row.id, {"reach": len(targets), "scheduledAt": scheduled_at})

    db.commit()

    return {"notice": notice(notice_row), "batchId": batch_row.id, "reach": len(targets), "scheduled": scheduled}





@router.get("/workbench/batches")

def list_batches(

    title: str = "",

    batch_id: str = Query(default="", alias="batchId"),

    status: str = "",

    from_ms: int = Query(default=0, alias="fromMs"),

    to_ms: int = Query(default=0, alias="toMs"),

    db: Session = Depends(get_db),

    session: CurrentSession = Depends(get_current_session),

) -> dict:

    if session.role not in {"teacher", "leader", "coordinator"}:

        raise HTTPException(status_code=403, detail="forbidden")

    rows = db.scalars(select(NoticeBatch).order_by(NoticeBatch.created_at.desc())).all()

    payload = [batch_with_read_stats(db, row) for row in rows]

    if title:

        payload = [item for item in payload if title in item["title"]]

    if batch_id:

        payload = [item for item in payload if batch_id in item["id"]]

    if status:

        payload = [item for item in payload if item.get("status") == status]

    if from_ms:

        payload = [item for item in payload if (item.get("createdAt") or 0) >= from_ms]

    if to_ms:

        payload = [item for item in payload if (item.get("createdAt") or 0) <= to_ms]

    return {"list": payload}





@router.post("/workbench/notices/scheduled/dispatch")

def dispatch_scheduled(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:

    if session.role != "teacher":

        raise HTTPException(status_code=403, detail="forbidden")

    return run_scheduled_dispatch(db, session)





def run_scheduled_dispatch(db: Session, session: CurrentSession) -> dict:

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    rows = db.scalars(select(NoticeBatch).order_by(NoticeBatch.created_at)).all()

    dispatched = 0

    for row in rows:

        schedule = (row.target_rule or {}).get("_schedule", {})

        if schedule.get("status") != "scheduled" or int(schedule.get("scheduledAt") or 0) > now_ms:

            continue

        notice_row = db.get(Notice, schedule.get("noticeId"))

        if not notice_row:

            continue

        current = db.get(Student, session.student_id)

        targets = [s for s in db.scalars(select(Student)).all() if match_rule(row.target_rule, s, session, current)]

        row.channels = dispatch_notice(db, notice_row, row.id, targets)

        row.target_rule = {

            **(row.target_rule or {}),

            "_schedule": {**schedule, "status": "sent", "targetCount": len(targets), "dispatchedAt": now_ms},

        }

        dispatched += 1

    audit(db, session, "notice_scheduled_dispatch", "notice_batches", {"dispatched": dispatched})

    db.commit()

    return {"ok": True, "dispatched": dispatched}





def batch_with_read_stats(db: Session, row: NoticeBatch) -> dict:

    payload = batch(row)

    read_count = db.scalar(

        select(func.count())

        .select_from(Message)

        .where(Message.batch_id == row.id, Message.read_at.is_not(None)),

    ) or 0

    payload["channels"] = [

        {**channel, "read": read_count} if channel.get("name") == "站内" else channel

        for channel in payload["channels"]

    ]

    return payload





def match_rule(rule: dict, student: Student, session: CurrentSession, current: Student | None) -> bool:

    if session.role == "coordinator":

        if not current or student.class_name != current.class_name:

            return False

    kind = (rule or {}).get("kind", "all")

    value = (rule or {}).get("value", "")

    if kind == "all":

        return True

    if kind == "grade":

        return student.grade == value

    if kind == "major":

        return value in student.major

    if kind == "class":

        return student.class_name == value

    if kind == "political":

        return value in (student.political_status or "")

    if kind == "extension":

        ext_key = (rule or {}).get("extKey", "")

        ext_val = (rule or {}).get("extValue", "")

        if ext_key and ext_val:

            return str((student.extension or {}).get(ext_key, "")) == ext_val

    return True


