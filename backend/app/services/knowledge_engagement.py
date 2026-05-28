"""知识库收藏、最近浏览、热门统计。"""

from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import KnowledgeFavorite, KnowledgeItem, KnowledgeRecentView
from app.services.serializers import knowledge


def record_recent_view(db: Session, student_id: str, item_id: str) -> None:
    db.execute(
        delete(KnowledgeRecentView).where(
            KnowledgeRecentView.student_id == student_id,
            KnowledgeRecentView.item_id == item_id,
        ),
    )
    db.add(KnowledgeRecentView(student_id=student_id, item_id=item_id, viewed_at=datetime.now(timezone.utc)))


def trim_recent_views(db: Session, student_id: str, keep: int = 30) -> None:
    rows = db.scalars(
        select(KnowledgeRecentView)
        .where(KnowledgeRecentView.student_id == student_id)
        .order_by(KnowledgeRecentView.viewed_at.desc()),
    ).all()
    for row in rows[keep:]:
        db.delete(row)


def list_favorites(db: Session, student_id: str) -> list[dict]:
    fav_ids = db.scalars(select(KnowledgeFavorite.item_id).where(KnowledgeFavorite.student_id == student_id)).all()
    if not fav_ids:
        return []
    rows = db.scalars(select(KnowledgeItem).where(KnowledgeItem.id.in_(fav_ids), KnowledgeItem.online.is_(True))).all()
    order = {item_id: index for index, item_id in enumerate(fav_ids)}
    rows.sort(key=lambda row: order.get(row.id, 999))
    return [knowledge(row) for row in rows]


def list_recent(db: Session, student_id: str, limit: int = 20) -> list[dict]:
    views = db.scalars(
        select(KnowledgeRecentView)
        .where(KnowledgeRecentView.student_id == student_id)
        .order_by(KnowledgeRecentView.viewed_at.desc())
        .limit(limit),
    ).all()
    if not views:
        return []
    item_ids = [view.item_id for view in views]
    rows = {row.id: row for row in db.scalars(select(KnowledgeItem).where(KnowledgeItem.id.in_(item_ids))).all()}
    return [knowledge(rows[item_id]) for item_id in item_ids if item_id in rows and rows[item_id].online]


def list_trending(db: Session, limit: int = 10) -> list[dict]:
    rows = db.scalars(
        select(KnowledgeItem)
        .where(KnowledgeItem.online.is_(True))
        .order_by(KnowledgeItem.hit_count.desc(), KnowledgeItem.updated_at.desc())
        .limit(limit),
    ).all()
    return [knowledge(row) for row in rows]


def favorite_ids(db: Session, student_id: str) -> set[str]:
    return set(db.scalars(select(KnowledgeFavorite.item_id).where(KnowledgeFavorite.student_id == student_id)).all())


def toggle_favorite(db: Session, student_id: str, item_id: str) -> dict:
    row = db.get(KnowledgeItem, item_id)
    if not row or not row.online:
        raise ValueError("knowledge not found")
    existing = db.get(KnowledgeFavorite, {"student_id": student_id, "item_id": item_id})
    if existing:
        db.delete(existing)
        return {"ok": True, "favorited": False}
    db.add(KnowledgeFavorite(student_id=student_id, item_id=item_id))
    return {"ok": True, "favorited": True}
