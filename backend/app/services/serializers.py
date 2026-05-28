from app.models import (
    AcademicPlan,
    AcademicProgress,
    Application,
    AuditLog,
    Honor,
    KnowledgeItem,
    Message,
    Notice,
    NoticeBatch,
    PartyProgress,
    Student,
    TemplateFile,
)
from app.services.common import dt_ms, mask_phone
from app.services.crypto_fields import decrypt_text, mask_id_card


def student_public(row: Student, role: str) -> dict:
    base = {
        "studentId": row.student_id,
        "role": row.role or "student",
        "name": row.name,
        "grade": row.grade,
        "major": row.major,
        "className": row.class_name,
        "nation": row.nation,
        "politicalStatus": row.political_status,
        "tutor": row.tutor,
        "extension": row.extension or {},
        "phoneMasked": mask_phone(row.phone),
    }
    if role == "teacher":
        base.update(
            {
                "phone": row.phone,
                "hometown": row.hometown,
                "idCardMasked": mask_id_card(decrypt_text(row.id_card_encrypted)) if row.id_card_encrypted else "",
            },
        )
    elif role == "leader":
        base.update({"hometown": f"{row.hometown[:1]}**" if row.hometown else ""})
    if role == "student":
        base.pop("tutor", None)
    return base


def knowledge(row: KnowledgeItem, q: str = "") -> dict:
    payload = {
        "id": row.id,
        "title": row.title,
        "category": row.category,
        "tags": row.tags or [],
        "summary": row.summary if not row.sensitive_hint else f"{row.summary}（详情请通过官方渠道查阅）",
        "body": row.body if not row.sensitive_hint else "",
        "officialLink": row.official_link or "",
        "sensitiveHint": row.sensitive_hint,
        "attachments": row.attachments or [],
        "updatedAt": dt_ms(row.updated_at),
        "hitCount": row.hit_count,
        "online": row.online,
    }
    if q and q.lower() in (row.title or "").lower():
        payload["matchReason"] = "标题匹配"
    elif q:
        payload["matchReason"] = "内容匹配"
    return payload


def template(row: TemplateFile) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "scene": row.scene,
        "format": row.format,
        "fileUrl": row.file_url or (f"/api/templates/{row.id}/download" if row.id else ""),
        "fileId": row.file_id or "",
    }


def notice(row: Notice) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "tags": row.tags or [],
        "summary": row.summary,
        "content": row.content,
        "source": row.source,
        "publishedAt": dt_ms(row.published_at),
    }


def message(row: Message) -> dict:
    return {
        "id": row.id,
        "studentId": row.student_id,
        "noticeId": row.notice_id,
        "title": row.title,
        "summary": row.summary,
        "batchId": row.batch_id,
        "channels": row.channels or [],
        "createdAt": dt_ms(row.created_at),
        "readAt": dt_ms(row.read_at),
    }


def application(row: Application) -> dict:
    return {
        "id": row.id,
        "studentId": row.student_id,
        "type": row.type,
        "subtype": row.subtype,
        "status": row.status,
        "createdAt": dt_ms(row.created_at),
        "form": row.form or {},
        "attachments": row.attachments or [],
        "teacherComment": row.teacher_comment,
        "decidedAt": dt_ms(row.decided_at),
        "auditTrail": row.audit_trail or [],
    }


def honor(row: Honor) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "winner": row.winner,
        "year": row.year,
        "major": row.major,
        "grade": row.grade,
        "category": row.category,
        "intro": row.intro,
    }


def honor_public(row: Honor, role: str) -> dict:
    payload = honor(row)
    attachments = row.attachments or []
    if role not in {"teacher", "leader"}:
        if row.visibility == "restricted":
            attachments = []
        else:
            attachments = [a for a in attachments if a.get("visibility") != "restricted"]
    payload.update({"visibility": row.visibility or "public", "online": row.online is not False, "attachments": attachments})
    return payload


def party(row: PartyProgress) -> dict:
    return {"studentId": row.student_id, "currentKey": row.current_key, "history": row.history or [], "tasks": row.tasks or []}


def academic_plan(row: AcademicPlan | None) -> dict | None:
    if not row:
        return None
    return {"key": row.key, "grade": row.grade, "major": row.major, "modules": row.modules or []}


def academic_progress(row: AcademicProgress | None) -> dict | None:
    if not row:
        return None
    return {
        "studentId": row.student_id,
        "modules": row.modules or [],
        "uploads": row.uploads or [],
        "courses": row.courses or [],
    }


def batch(row: NoticeBatch) -> dict:
    target_rule = row.target_rule or {}
    schedule = target_rule.get("_schedule", {})
    return {
        "id": row.id,
        "title": row.title,
        "targetRule": {key: value for key, value in target_rule.items() if not key.startswith("_")},
        "status": schedule.get("status", "sent"),
        "scheduledAt": schedule.get("scheduledAt"),
        "noticeId": schedule.get("noticeId"),
        "createdAt": dt_ms(row.created_at),
        "channels": row.channels or [],
    }


def audit_log(row: AuditLog) -> dict:
    return {
        "id": row.id,
        "at": dt_ms(row.at),
        "actorId": row.actor_id,
        "role": row.role,
        "action": row.action,
        "target": row.target,
        "detail": row.detail or {},
    }
