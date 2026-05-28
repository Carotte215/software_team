from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import CurrentSession, get_current_session
from app.models import KnowledgeFavorite, KnowledgeItem, KnowledgeMissKeyword, TemplateFile
from app.schemas import KnowledgeCreate, KnowledgeOnlinePut, KnowledgeUpdate
from app.services.common import audit, uid
from app.services.file_storage import attachment_file_ids, cleanup_orphan_files
from app.services.knowledge_engagement import favorite_ids, list_favorites, list_recent, list_trending, record_recent_view, toggle_favorite, trim_recent_views
from app.services.permissions import COORDINATOR, TEACHER, require_roles
from app.services.serializers import knowledge, template

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("")
def list_knowledge(
    q: str = "",
    category: str = "全部",
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(KnowledgeItem).where(KnowledgeItem.online.is_(True))
    if category and category != "全部":
        stmt = stmt.where(KnowledgeItem.category == category)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                KnowledgeItem.title.ilike(like),
                KnowledgeItem.summary.ilike(like),
                KnowledgeItem.body.ilike(like),
                KnowledgeItem.official_link.ilike(like),
            ),
        )
    rows = db.scalars(stmt).all()
    if q:
        rows = rank_knowledge_rows(rows, q)
    else:
        rows = sorted(rows, key=lambda row: (-(row.hit_count or 0), row.updated_at or row.created_at), reverse=False)
    categories = ["全部", *db.scalars(select(KnowledgeItem.category).distinct()).all()]
    templates = db.scalars(select(TemplateFile).order_by(TemplateFile.name)).all()
    payload = {"list": [knowledge(row, q=q) for row in rows], "categories": categories, "templates": [template(row) for row in templates]}
    if q and not rows:
        payload["searchMeta"] = {
            "noResult": True,
            "hint": "未找到匹配的政策条目。建议换个关键词，或联系辅导员 / 学院学生工作办公室（010-62513007）咨询。",
            "keyword": q,
        }
    return payload


def rank_knowledge_rows(rows: list[KnowledgeItem], q: str) -> list[KnowledgeItem]:
    """FR1-3：标准答案/标题/标签优先，而非简单按点击量。"""
    needle = q.strip().lower()

    def score(row: KnowledgeItem) -> tuple[int, int]:
        title = (row.title or "").lower()
        summary = (row.summary or "").lower()
        body = (row.body or "").lower()
        tags = [str(tag).lower() for tag in (row.tags or [])]
        points = 0
        if title == needle:
            points += 100
        elif needle in title:
            points += 60
        if any(needle in tag for tag in tags):
            points += 40
        if needle in summary:
            points += 25
        if row.official_link:
            points += 15
        if needle in body:
            points += 10
        return points, row.hit_count or 0

    return sorted(rows, key=lambda row: score(row), reverse=True)


@router.post("")
def create_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    row = KnowledgeItem(
        id=uid("k"),
        title=payload.title,
        category=payload.category,
        tags=payload.tags,
        summary=payload.summary,
        body=payload.body,
        official_link=payload.official_link,
        sensitive_hint=payload.sensitive_hint,
        attachments=payload.attachments,
    )
    db.add(row)
    audit(db, session, "knowledge_create", row.id)
    db.commit()
    return knowledge(row)


@router.get("/admin/list")
def list_knowledge_admin(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    if session.role not in {"teacher", "leader", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    rows = db.scalars(select(KnowledgeItem).order_by(KnowledgeItem.updated_at.desc())).all()
    return {"list": [knowledge(row) for row in rows]}


@router.get("/export")
def export_knowledge(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)):
    import csv
    from io import StringIO
    from urllib.parse import quote

    from fastapi.responses import Response

    require_roles(session, TEACHER)
    rows = db.scalars(select(KnowledgeItem).order_by(KnowledgeItem.category, KnowledgeItem.title)).all()
    fp = StringIO()
    writer = csv.writer(fp)
    writer.writerow(["id", "标题", "分类", "标签", "摘要", "上线", "命中"])
    for row in rows:
        writer.writerow([row.id, row.title, row.category, ",".join(row.tags or []), row.summary, row.online, row.hit_count])
    filename = quote("知识库导出.csv")
    return Response(
        "\ufeff" + fp.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.put("/{item_id}")
def update_knowledge(
    item_id: str,
    payload: KnowledgeUpdate,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    if session.role not in {"teacher", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    row = db.get(KnowledgeItem, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="knowledge not found")
    old_file_ids = attachment_file_ids(row.attachments)
    row.title = payload.title
    row.category = payload.category
    row.tags = payload.tags
    row.summary = payload.summary
    row.body = payload.body
    row.official_link = payload.official_link
    row.sensitive_hint = payload.sensitive_hint
    row.attachments = payload.attachments
    row.online = payload.online
    audit(db, session, "knowledge_update", item_id)
    db.commit()
    cleanup_orphan_files(db, old_file_ids - attachment_file_ids(row.attachments))
    return knowledge(row)


@router.post("/{item_id}/online")
def set_knowledge_online(
    item_id: str,
    payload: KnowledgeOnlinePut,
    db: Session = Depends(get_db),
    session: CurrentSession = Depends(get_current_session),
) -> dict:
    if session.role not in {"teacher", "coordinator"}:
        raise HTTPException(status_code=403, detail="forbidden")
    row = db.get(KnowledgeItem, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="knowledge not found")
    row.online = payload.online
    audit(db, session, "knowledge_online" if payload.online else "knowledge_offline", item_id)
    db.commit()
    return knowledge(row)


@router.post("/miss")
def record_miss(payload: dict, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    keyword = str(payload.get("keyword", "")).strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword required")
    row = db.get(KnowledgeMissKeyword, keyword)
    if row:
        row.count += 1
        row.last_student_id = session.student_id
    else:
        db.add(KnowledgeMissKeyword(keyword=keyword, count=1, last_student_id=session.student_id))
    audit(db, session, "knowledge_miss", keyword)
    db.commit()
    return {"ok": True}


@router.get("/favorites")
def knowledge_favorites(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    return {"list": list_favorites(db, session.student_id)}


@router.get("/recent")
def knowledge_recent(db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    return {"list": list_recent(db, session.student_id)}


@router.get("/trending")
def knowledge_trending(db: Session = Depends(get_db)) -> dict:
    return {"list": list_trending(db)}


@router.post("/favorites/{item_id}")
def add_favorite(item_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    try:
        result = toggle_favorite(db, session.student_id, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    audit(db, session, "knowledge_favorite_toggle", item_id, result)
    db.commit()
    return result


@router.delete("/favorites/{item_id}")
def remove_favorite(item_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(KnowledgeFavorite, {"student_id": session.student_id, "item_id": item_id})
    if row:
        db.delete(row)
        audit(db, session, "knowledge_favorite_remove", item_id)
        db.commit()
    return {"ok": True, "favorited": False}


@router.get("/{item_id}")
def get_knowledge(item_id: str, db: Session = Depends(get_db), session: CurrentSession = Depends(get_current_session)) -> dict:
    row = db.get(KnowledgeItem, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="knowledge not found")
    row.hit_count += 1
    record_recent_view(db, session.student_id, item_id)
    trim_recent_views(db, session.student_id)
    audit(db, session, "knowledge_read", item_id)
    db.commit()
    payload = knowledge(row)
    payload["favorited"] = item_id in favorite_ids(db, session.student_id)
    return payload
