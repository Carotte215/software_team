"""党团阶段推进校验与政治面貌联动。"""

from fastapi import HTTPException

from app.models import LeagueProgress, PartyProgress, Student
from app.services.party_official_data import LEAGUE_FLOW_STAGES, LEAGUE_STEPS, OFFICIAL_FLOW_STAGES, OFFICIAL_STEPS

PARTY_POLITICAL_BY_STAGE = {
    "applicant": "入党申请人",
    "activist": "入党积极分子",
    "candidate": "发展对象",
    "probationary": "中共预备党员",
    "member": "中共党员",
}

LEAGUE_POLITICAL_BY_STAGE = {
    "l_apply": "入团积极分子",
    "l_activist": "入团积极分子",
    "l_develop": "发展对象",
    "l_member": "共青团员",
}


def stage_order(stages: list[dict], key: str) -> int:
    return next((item["order"] for item in stages if item["key"] == key), 0)


def validate_party_advance(row: PartyProgress, next_key: str, *, force: bool = False) -> None:
    stages = [{"key": item["key"], "order": item["order"]} for item in OFFICIAL_FLOW_STAGES]
    current_order = stage_order(stages, row.current_key)
    next_order = stage_order(stages, next_key)
    if next_order <= 0 or next_key not in {item["key"] for item in OFFICIAL_FLOW_STAGES}:
        raise HTTPException(status_code=400, detail="无效的目标阶段")
    if next_order < current_order and not force:
        raise HTTPException(status_code=400, detail="不可回退阶段，如需回退请在备注中说明并使用 force=true")
    if next_order == current_order:
        raise HTTPException(status_code=400, detail="目标阶段与当前阶段相同")
    if not force:
        pending = unverified_current_steps(row)
        if pending:
            names = "、".join(pending[:3])
            raise HTTPException(
                status_code=400,
                detail=f"当前阶段仍有 {len(pending)} 个环节未确认（{names}…），请先确认或传 force=true",
            )


def validate_league_advance(row: LeagueProgress, next_key: str, *, force: bool = False) -> None:
    stages = [{"key": item["key"], "order": item["order"]} for item in LEAGUE_FLOW_STAGES]
    current_order = stage_order(stages, row.current_key)
    next_order = stage_order(stages, next_key)
    if next_order <= 0 or next_key not in {item["key"] for item in LEAGUE_FLOW_STAGES}:
        raise HTTPException(status_code=400, detail="无效的目标阶段")
    if next_order < current_order and not force:
        raise HTTPException(status_code=400, detail="不可回退阶段，如需回退请传 force=true")
    if next_order == current_order:
        raise HTTPException(status_code=400, detail="目标阶段与当前阶段相同")
    if not force:
        pending = unverified_league_steps(row)
        if pending:
            raise HTTPException(status_code=400, detail=f"当前阶段仍有 {len(pending)} 个环节未确认，请先确认或传 force=true")


def unverified_current_steps(row: PartyProgress) -> list[str]:
    verified = set(row.verified_steps or [])
    completed = set(row.completed_steps or [])
    names = []
    for step in OFFICIAL_STEPS:
        if step["stageKey"] != row.current_key:
            continue
        if step["id"] in completed and step["id"] not in verified:
            names.append(step["name"])
    return names


def unverified_league_steps(row: LeagueProgress) -> list[str]:
    verified = set(row.verified_steps or [])
    completed = set(row.completed_steps or [])
    names = []
    for step in LEAGUE_STEPS:
        if step["stageKey"] != row.current_key:
            continue
        if step["id"] in completed and step["id"] not in verified:
            names.append(step["name"])
    return names


def sync_political_for_party(student: Student, stage_key: str) -> None:
    label = PARTY_POLITICAL_BY_STAGE.get(stage_key)
    if label:
        student.political_status = label


def sync_political_for_league(student: Student, stage_key: str) -> None:
    label = LEAGUE_POLITICAL_BY_STAGE.get(stage_key)
    if label and student.political_status in {"", "群众", "入团积极分子", "共青团员"}:
        student.political_status = label
