"""党团环节材料与思想汇报归档。"""

from datetime import datetime, timezone

from fastapi import HTTPException

from app.models import LeagueProgress, PartyProgress
from app.services.common import now_ms, uid
from app.services.file_storage import attachment_file_ids, cleanup_orphan_files
from app.services.party_official_data import LEAGUE_STEPS, OFFICIAL_STEPS, STEP_MATERIALS_MAP, enrich_official_step

PARTY_STEPS_BY_ID = {step["id"]: step for step in OFFICIAL_STEPS}
LEAGUE_STEPS_BY_ID = {step["id"]: step for step in LEAGUE_STEPS}


def enrich_party_step(step: dict, materials: dict | None = None) -> dict:
    files = list((materials or {}).get(step["id"], []) or [])
    base = enrich_official_step(step)
    catalog = base.get("materialCatalog") or []
    return {**base, "materials": files, "requiresUpload": bool(catalog)}


def enrich_league_step(step: dict, materials: dict | None = None) -> dict:
    files = list((materials or {}).get(step["id"], []) or [])
    base = enrich_official_step(step, league=True)
    catalog = base.get("materialCatalog") or []
    return {**base, "materials": files, "requiresUpload": bool(catalog)}


def validate_step_id(step_id: str, *, league: bool = False) -> dict:
    catalog = LEAGUE_STEPS_BY_ID if league else PARTY_STEPS_BY_ID
    step = catalog.get(step_id)
    if not step:
        raise HTTPException(status_code=404, detail="step not found")
    return step


def ensure_step_upload_allowed(row: PartyProgress | LeagueProgress, step_id: str, *, league: bool = False) -> None:
    validate_step_id(step_id, league=league)
    catalog = STEP_MATERIALS_MAP.get(step_id, [])
    if not catalog:
        return
    materials = (row.step_materials or {}).get(step_id, [])
    if not materials:
        names = "、".join(catalog[:2])
        raise HTTPException(status_code=400, detail=f"请先上传环节材料（{names}…）")


def attach_step_materials(
    row: PartyProgress | LeagueProgress,
    step_id: str,
    attachments: list[dict],
    *,
    league: bool = False,
) -> dict:
    validate_step_id(step_id, league=league)
    if not attachments:
        raise HTTPException(status_code=400, detail="attachments required")
    store = dict(row.step_materials or {})
    merged = list(store.get(step_id, []) or [])
    seen = {item.get("id") for item in merged}
    for item in attachments:
        file_id = str(item.get("id") or item.get("fileId") or "").strip()
        if not file_id or file_id in seen:
            continue
        merged.append(item)
        seen.add(file_id)
    store[step_id] = merged
    row.step_materials = store
    return {"ok": True, "stepId": step_id, "materials": merged}


def detach_step_material(row: PartyProgress | LeagueProgress, step_id: str, file_id: str) -> dict:
    store = dict(row.step_materials or {})
    items = list(store.get(step_id, []) or [])
    kept = [item for item in items if str(item.get("id") or item.get("fileId") or "") != file_id]
    if len(kept) == len(items):
        raise HTTPException(status_code=404, detail="material not found")
    if kept:
        store[step_id] = kept
    else:
        store.pop(step_id, None)
    row.step_materials = store
    return {"ok": True, "removed": file_id}


def collect_step_file_ids(row: PartyProgress | LeagueProgress) -> set[str]:
    from app.services.file_storage import progress_attachment_ids

    return progress_attachment_ids(row)


def current_quarter_label(when: datetime | None = None) -> str:
    when = when or datetime.now(timezone.utc)
    quarter = (when.month - 1) // 3 + 1
    return f"{when.year}-Q{quarter}"


def submit_thought_report(row: PartyProgress, payload: dict) -> dict:
    content = str(payload.get("content", "")).strip()
    if len(content) < 50:
        raise HTTPException(status_code=400, detail="思想汇报正文不少于 50 字")
    quarter = str(payload.get("quarter", "")).strip() or current_quarter_label()
    attachments = list(payload.get("attachments") or [])
    reports = list(row.thought_reports or [])
    if any(item.get("quarter") == quarter for item in reports):
        raise HTTPException(status_code=400, detail=f"{quarter} 思想汇报已提交，请勿重复")
    entry = {
        "id": uid("tr"),
        "quarter": quarter,
        "title": str(payload.get("title", "")).strip() or f"{quarter.replace('-Q', '年第')}季度思想汇报",
        "content": content,
        "attachments": attachments,
        "submittedAt": now_ms(),
    }
    row.thought_reports = [entry, *reports]
    return entry
