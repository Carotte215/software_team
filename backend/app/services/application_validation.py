"""办事申请服务端校验。"""

from fastapi import HTTPException

LEAVE_SUBTYPES = {"事假", "病假", "其他"}


def validate_application_payload(app_type: str, subtype: str, form: dict) -> None:
    app_type = (app_type or "").strip()
    subtype = (subtype or "").strip()
    form = form or {}

    if app_type == "盖章申请":
        if str(form.get("offlineHandoff", "")).lower() in {"1", "true", "yes"} and not str(form.get("reason", "")).strip():
            raise HTTPException(status_code=400, detail="涉密转线下须在申请说明中备注流转方式")
        return

    if app_type == "请假申请":
        if subtype and subtype not in LEAVE_SUBTYPES:
            raise HTTPException(status_code=400, detail="请假类型须为：事假、病假、其他")
        if not str(form.get("reason", "")).strip():
            raise HTTPException(status_code=400, detail="请假申请须填写事由")
        if not str(form.get("startDate", "")).strip() or not str(form.get("endDate", "")).strip():
            raise HTTPException(status_code=400, detail="请假申请须填写起止日期")
        if str(form.get("startDate", "")) > str(form.get("endDate", "")):
            raise HTTPException(status_code=400, detail="请假开始日期不能晚于结束日期")
        return

    if app_type != "证明申请":
        return

    if subtype == "党员证明":
        missing = [name for name, key in (
            ("身份证号", "idCard"),
            ("入党时间", "partyJoinDate"),
            ("所在党支部", "partyBranch"),
        ) if not str(form.get(key, "")).strip()]
        if missing:
            raise HTTPException(status_code=400, detail=f"党员证明须填写：{'、'.join(missing)}")
    elif subtype == "团员证明":
        missing = [name for name, key in (
            ("身份证号", "idCard"),
            ("入团时间", "leagueJoinDate"),
            ("团员编号", "memberNo"),
        ) if not str(form.get(key, "")).strip()]
        if missing:
            raise HTTPException(status_code=400, detail=f"团员证明须填写：{'、'.join(missing)}")
    elif subtype == "在读证明":
        if not str(form.get("reason", "")).strip():
            raise HTTPException(status_code=400, detail="在读证明须填写申请事由")
