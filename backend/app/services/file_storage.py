import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Application, Honor, KnowledgeItem, LeagueProgress, PartyProgress, TemplateFile


def storage_root() -> Path:
    root = Path(get_settings().upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def meta_path(file_id: str) -> Path:
    return storage_root() / f"{file_id}.json"


def data_path(file_id: str, suffix: str) -> Path:
    return storage_root() / f"{file_id}{suffix}"


def attachment_file_ids(items: list[dict] | None) -> set[str]:
    result: set[str] = set()
    for item in items or []:
        file_id = str(item.get("id") or item.get("fileId") or "").strip()
        if file_id:
            result.add(file_id)
    return result


def cleanup_orphan_files(db: Session, file_ids: set[str] | list[str] | tuple[str, ...]) -> list[str]:
    deleted: list[str] = []
    for raw_file_id in file_ids:
        file_id = str(raw_file_id or "").strip()
        if not file_id or file_is_referenced(db, file_id):
            continue
        delete_file_assets(file_id)
        deleted.append(file_id)
    return deleted


def progress_attachment_ids(row: PartyProgress | LeagueProgress) -> set[str]:
    result: set[str] = set()
    for items in (row.step_materials or {}).values():
        result.update(attachment_file_ids(items))
    if isinstance(row, PartyProgress):
        for report in row.thought_reports or []:
            result.update(attachment_file_ids(report.get("attachments")))
    return result


def file_is_referenced(db: Session, file_id: str) -> bool:
    if db.scalars(select(TemplateFile).where(TemplateFile.file_id == file_id)).first():
        return True
    for row in db.scalars(select(KnowledgeItem.attachments)).all():
        if file_id in attachment_file_ids(row):
            return True
    for row in db.scalars(select(Honor.attachments)).all():
        if file_id in attachment_file_ids(row):
            return True
    for row in db.scalars(select(Application.attachments)).all():
        if file_id in attachment_file_ids(row):
            return True
    for row in db.scalars(select(PartyProgress)).all():
        if file_id in progress_attachment_ids(row):
            return True
    for row in db.scalars(select(LeagueProgress)).all():
        if file_id in progress_attachment_ids(row):
            return True
    return False


def delete_file_assets(file_id: str) -> None:
    meta_file = meta_path(file_id)
    suffix = ""
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            suffix = str(meta.get("suffix", "") or "")
        except (OSError, json.JSONDecodeError):
            suffix = ""
    if suffix:
        data_path(file_id, suffix).unlink(missing_ok=True)
    else:
        for candidate in storage_root().glob(f"{file_id}.*"):
            if candidate.name != f"{file_id}.json":
                candidate.unlink(missing_ok=True)
    meta_file.unlink(missing_ok=True)
