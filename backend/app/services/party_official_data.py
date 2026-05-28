"""党团平台官方依据：发展党员工作程序（29 环节）、人大 2025-2026 校历、证明模板。"""

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "party"

OFFICIAL_ASSETS = {
    "flowchart": {
        "id": "doc_flowchart",
        "title": "发展党员工作程序图",
        "description": "5 个阶段、29 个环节，依据《中国共产党发展党员工作细则》及学院组织工作常用流程整理。",
        "fileName": "flowchart-party-development.png",
        "contentType": "image/png",
    },
    "calendar": {
        "id": "doc_calendar",
        "title": "中国人民大学 2025-2026 学年校历",
        "description": "秋季学期 2025-09-08 至 2026-01-11；春季学期 2026-03-02 至 2026-07-12。党团活动、社会实践请对照校历安排。",
        "fileName": "calendar-ruc-2025-2026.png",
        "contentType": "image/png",
    },
    "party_cert": {
        "id": "doc_party_cert",
        "title": "党员证明模板",
        "description": "信息学院党委开具党员证明的标准格式，办理前请核对抬头、入党时间与组织关系所在支部。",
        "fileName": "party-member-certificate.docx",
        "contentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    "league_cert": {
        "id": "doc_league_cert",
        "title": "团员证明模板",
        "description": "信息学院团委开具团员证明的标准格式，需填写学号、入团时间与团员编号。",
        "fileName": "league-member-certificate.docx",
        "contentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
}

# 学院官方联系与依据（来自党员/团员证明模板、流程图说明）
OFFICIAL_META = {
    "legalBasis": "《中国共产党发展党员工作细则》",
    "leagueBasis": "《中国共产主义青年团发展团员工作细则》及学院团委规定",
    "partyOrg": "中国人民大学信息学院党委",
    "leagueOrg": "中国人民大学信息学院团委",
    "contactName": "组织工作咨询",
    "contactPhone": "010-62513007",
    "flowSummary": "5 个阶段 · 29 个环节",
    "leagueFlowSummary": "4 个阶段 · 8 个环节",
    "semesters": [
        {"term": "fall", "label": "2025-2026 学年秋季学期", "start": "2025-09-08", "end": "2026-01-11"},
        {"term": "spring", "label": "2025-2026 学年春季学期", "start": "2026-03-02", "end": "2026-07-12"},
    ],
}

STEP_TIME_RULES = {
    "step_02": "收到入党申请书后一个月内完成谈话并记录",
    "step_05": "培养考察期一般不少于一年，每季度至少一篇思想汇报",
    "step_10": "短期集中培训不少于三天（或二十四个学时）并结业",
    "step_13": "接收预备党员公示不少于五个工作日",
    "step_17": "党委审批应在三个月内完成（特殊情况不超过六个月）",
    "step_22": "预备期一年，从支部大会通过预备党员之日算起",
    "step_27": "转正审批应在三个月内作出决定",
    "l_step_04": "培养考察与志愿服务时长以团支部公示为准",
}

CERT_FIELD_SPECS = {
    "party": [
        {"key": "name", "label": "姓名", "hint": "与身份证、学籍信息一致"},
        {"key": "studentId", "label": "学号", "hint": "中国人民大学学籍号"},
        {"key": "idCard", "label": "身份证号", "hint": "证明模板必填项，平台加密存储"},
        {"key": "major", "label": "专业", "hint": "如：计算机科学与技术"},
        {"key": "grade", "label": "年级", "hint": "如：2024 级本科/硕士/博士"},
        {"key": "partyJoinDate", "label": "入党时间", "hint": "以支部大会通过其为预备党员之日为准（YYYY-MM-DD）"},
        {"key": "partyBranch", "label": "所在党支部", "hint": "组织关系所在支部全称，如：信息学院学生 XX 党支部"},
    ],
    "league": [
        {"key": "name", "label": "姓名", "hint": "与身份证、学籍信息一致"},
        {"key": "studentId", "label": "学号", "hint": "中国人民大学学籍号"},
        {"key": "idCard", "label": "身份证号", "hint": "证明模板必填项"},
        {"key": "className", "label": "班级", "hint": "如：2024 级计算机 1 班"},
        {"key": "leagueJoinDate", "label": "入团时间", "hint": "以团支部大会通过之日为准（YYYY-MM-DD）"},
        {"key": "memberNo", "label": "团员编号", "hint": "团员证或档案中的编号"},
    ],
}

THOUGHT_REPORT_GUIDE = {
    "title": "思想汇报撰写要点（依据培养考察要求）",
    "frequency": "积极分子、预备党员一般每季度至少提交一篇",
    "sections": [
        "对党的认识与入党/转正动机",
        "本季度理论学习、党团活动参与情况",
        "学业科研、社会实践与志愿服务",
        "自身不足与今后努力方向",
    ],
    "templateId": "tpl_report",
    "minLength": 50,
}

# 与数据库 party_stages.stage_key 对齐；macroStage 对应官方流程图五大阶段标题
OFFICIAL_FLOW_STAGES = [
    {
        "key": "applicant",
        "name": "入党申请人",
        "desc": "接受教育引导，递交入党申请书，党组织派人谈话并留存记录。",
        "order": 1,
        "macroStage": "申请与谈话",
        "durationDays": 30,
        "remindBeforeDays": 7,
        "material": "入党申请书（手写或打印签名）、谈话记录表",
    },
    {
        "key": "activist",
        "name": "入党积极分子确定",
        "desc": "经团支部推优、支委会讨论并报党委备案，指定培养联系人，开展一年以上培养考察。",
        "order": 2,
        "macroStage": "入党积极分子确定",
        "durationDays": 365,
        "remindBeforeDays": 30,
        "material": "推优表、培养考察登记表、思想汇报（每季度）、培养联系人考察意见",
    },
    {
        "key": "candidate",
        "name": "发展对象确定",
        "desc": "支委会听取意见后讨论，报党委备案；确定入党介绍人，完成政治审查与短期集中培训。",
        "order": 3,
        "macroStage": "发展对象确定",
        "durationDays": 90,
        "remindBeforeDays": 14,
        "material": "发展对象备案表、政审材料、培训结业证书、公示记录",
    },
    {
        "key": "probationary",
        "name": "预备党员接收与转正",
        "desc": "党委预审、公示、支部大会接收预备党员；预备期内教育考察，期满提交转正申请并完成审批。",
        "order": 4,
        "macroStage": "预备党员接收 · 教育考察与转正",
        "durationDays": 365,
        "remindBeforeDays": 30,
        "material": "入党志愿书、预备党员考察表、转正申请书、支部大会决议、党委审批材料",
    },
    {
        "key": "member",
        "name": "正式党员",
        "desc": "转正审批通过，材料归档，进入正式党员教育管理。",
        "order": 5,
        "macroStage": "正式党员",
        "durationDays": 0,
        "remindBeforeDays": 0,
        "material": "党员档案归档清单、组织关系转接材料（如需）",
    },
]

# 官方流程图 29 环节；stageKey 映射到平台五大阶段
OFFICIAL_STEPS = [
    {"id": "step_01", "order": 1, "stageKey": "applicant", "name": "教育引导", "detail": "开展党的基本知识教育，引导向党组织靠拢。"},
    {"id": "step_02", "order": 2, "stageKey": "applicant", "name": "接收入党申请书并派人谈话", "detail": "收到申请书后一个月内，党支部书记或组织委员同本人谈话并记录。"},
    {"id": "step_03", "order": 3, "stageKey": "activist", "name": "确定入党积极分子并报党委备案", "detail": "经推优、支委会讨论，报上级党委备案。"},
    {"id": "step_04", "order": 4, "stageKey": "activist", "name": "指定培养联系人并进行培养教育", "detail": "指定一至两名培养联系人，制定培养计划。"},
    {"id": "step_05", "order": 5, "stageKey": "activist", "name": "考察", "detail": "培养考察期一般不少于一年，定期思想汇报与考察登记。"},
    {"id": "step_06", "order": 6, "stageKey": "candidate", "name": "支委会听取意见后讨论", "detail": "听取培养联系人、党员和群众意见，讨论是否列为发展对象。"},
    {"id": "step_07", "order": 7, "stageKey": "candidate", "name": "报党委备案后确定发展对象", "detail": "报具有审批权限的基层党委备案。"},
    {"id": "step_08", "order": 8, "stageKey": "candidate", "name": "确定入党介绍人", "detail": "一般应由两名正式党员担任介绍人。"},
    {"id": "step_09", "order": 9, "stageKey": "candidate", "name": "政治审查", "detail": "对本人及主要社会关系进行政治审查，形成结论性材料。"},
    {"id": "step_10", "order": 10, "stageKey": "candidate", "name": "短期集中培训", "detail": "发展对象应参加不少于三天（或二十四个学时）的集中培训并结业。"},
    {"id": "step_11", "order": 11, "stageKey": "probationary", "name": "支委会听取意见后讨论", "detail": "讨论接收预备党员事宜，形成审查意见。"},
    {"id": "step_12", "order": 12, "stageKey": "probationary", "name": "报党委预审", "detail": "支委会上报预审材料，党委审查后出具书面意见。"},
    {"id": "step_13", "order": 13, "stageKey": "probationary", "name": "公示", "detail": "对拟接收预备党员进行不少于五个工作日的公示。"},
    {"id": "step_14", "order": 14, "stageKey": "probationary", "name": "召开支部大会讨论接收预备党员", "detail": "有表决权的到会人数须超过应到会人数半数，无记名投票表决。"},
    {"id": "step_15", "order": 15, "stageKey": "probationary", "name": "将有关材料报党委", "detail": "上报入党志愿书等完整材料。"},
    {"id": "step_16", "order": 16, "stageKey": "probationary", "name": "党委委员或组织员与发展对象谈话", "detail": "作进一步了解和审查。"},
    {"id": "step_17", "order": 17, "stageKey": "probationary", "name": "党委审批", "detail": "三个月内完成审批，特殊情况不超过六个月。"},
    {"id": "step_18", "order": 18, "stageKey": "probationary", "name": "党委审批结果通知党支部", "detail": "书面通知审批结果。"},
    {"id": "step_19", "order": 19, "stageKey": "probationary", "name": "报上级党委组织部门备案", "detail": "预备党员接收情况报上级组织部门备案。"},
    {"id": "step_20", "order": 20, "stageKey": "probationary", "name": "编入党支部和党小组", "detail": "参加党的组织生活，接受教育考察。"},
    {"id": "step_21", "order": 21, "stageKey": "probationary", "name": "入党宣誓", "detail": "在正式场合举行入党宣誓仪式。"},
    {"id": "step_22", "order": 22, "stageKey": "probationary", "name": "教育和考察", "detail": "预备期一年，继续考察并填写考察登记表。"},
    {"id": "step_23", "order": 23, "stageKey": "probationary", "name": "接收转正申请、征求意见并审查", "detail": "预备期满前提交转正申请书，支委会审查。"},
    {"id": "step_24", "order": 24, "stageKey": "probationary", "name": "公示", "detail": "对拟转正的预备党员进行公示。"},
    {"id": "step_25", "order": 25, "stageKey": "probationary", "name": "召开支部大会讨论预备党员转正", "detail": "讨论是否按期转正、延长预备期或取消资格。"},
    {"id": "step_26", "order": 26, "stageKey": "probationary", "name": "将有关材料报党委", "detail": "上报转正相关材料。"},
    {"id": "step_27", "order": 27, "stageKey": "probationary", "name": "党委审批", "detail": "三个月内作出转正、延长或取消的决定。"},
    {"id": "step_28", "order": 28, "stageKey": "probationary", "name": "党委审批结果通知党支部", "detail": "党支部及时通知本人并在党员大会上宣布。"},
    {"id": "step_29", "order": 29, "stageKey": "member", "name": "存档", "detail": "党员材料归入人事档案或党员档案专卷。"},
]

# Phase 1/2：环节 ↔ 材料清单映射（学生需上传扫描件/ PDF 的环节）
STEP_MATERIALS_MAP = {
    "step_01": ["党的基础知识学习记录", "向党组织靠拢登记表"],
    "step_02": ["入党申请书（签名扫描件）", "谈话记录表"],
    "step_03": ["团支部推优表", "支委会会议记录", "积极分子备案表"],
    "step_04": ["培养联系人登记表", "培养计划"],
    "step_05": ["思想汇报", "培养考察登记表"],
    "step_06": ["支委会会议记录", "群众意见汇总"],
    "step_07": ["发展对象备案表"],
    "step_08": ["入党介绍人登记表"],
    "step_09": ["政审函调材料", "政审结论"],
    "step_10": ["集中培训结业证书", "培训登记表"],
    "step_11": ["支委会审查意见", "发展对象审查表"],
    "step_12": ["预审材料清单", "入党志愿书草稿"],
    "step_13": ["公示截图或照片", "公示情况说明"],
    "step_14": ["支部大会表决记录", "接收预备党员决议"],
    "step_15": ["入党志愿书", "支部大会决议"],
    "step_16": ["党委委员谈话记录"],
    "step_17": ["党委审批意见"],
    "step_18": ["审批结果通知"],
    "step_19": ["上级组织部门备案表"],
    "step_20": ["编入支部登记表"],
    "step_21": ["入党宣誓签到或照片"],
    "step_22": ["预备党员考察表", "思想汇报"],
    "step_23": ["转正申请书", "群众意见记录"],
    "step_24": ["转正公示记录"],
    "step_25": ["转正支部大会表决记录"],
    "step_26": ["转正材料上报清单"],
    "step_27": ["党委转正审批意见"],
    "step_28": ["转正结果通知"],
    "step_29": ["党员档案归档清单"],
    "l_step_01": ["入团申请书（签名扫描件）"],
    "l_step_02": ["团课学习记录", "青年大学习截图"],
    "l_step_03": ["入团积极分子备案表"],
    "l_step_04": ["培养考察表", "志愿服务时长证明"],
    "l_step_05": ["评议表", "公示记录"],
    "l_step_06": ["审批表", "上级团委批复"],
    "l_step_08": ["团员证复印件", "志愿书归档回执"],
}

LEAGUE_FLOW_STAGES = [
    {"key": "l_apply", "name": "入团申请", "desc": "递交入团申请书，参加团课学习与团支部活动。", "order": 1},
    {"key": "l_activist", "name": "入团积极分子", "desc": "团支部培养考察，完成志愿服务时长等要求（以团支部公示为准）。", "order": 2},
    {"key": "l_develop", "name": "发展对象", "desc": "支委会（团支委）评议、公示与上级团委审批。", "order": 3},
    {"key": "l_member", "name": "共青团员", "desc": "入团宣誓、团员证与档案归档。", "order": 4},
]

LEAGUE_STEPS = [
    {"id": "l_step_01", "order": 1, "stageKey": "l_apply", "name": "提交入团申请书", "detail": "向团支部提交书面申请，说明入团动机。"},
    {"id": "l_step_02", "order": 2, "stageKey": "l_apply", "name": "参加团课学习", "detail": "完成团支部组织的团课与青年大学习要求。"},
    {"id": "l_step_03", "order": 3, "stageKey": "l_activist", "name": "确定入团积极分子", "detail": "团支部讨论并报上级团组织备案。"},
    {"id": "l_step_04", "order": 4, "stageKey": "l_activist", "name": "培养考察与志愿服务", "detail": "按要求完成志愿时长、社会实践等（参考校历与社会实践安排）。"},
    {"id": "l_step_05", "order": 5, "stageKey": "l_develop", "name": "支部评议与公示", "detail": "团支委会评议并公示拟发展对象。"},
    {"id": "l_step_06", "order": 6, "stageKey": "l_develop", "name": "上级团委审批", "detail": "报学院团委或校团委审批。"},
    {"id": "l_step_07", "order": 7, "stageKey": "l_member", "name": "入团宣誓", "detail": "在团支部大会上举行入团宣誓。"},
    {"id": "l_step_08", "order": 8, "stageKey": "l_member", "name": "档案归档", "detail": "团员证、志愿书等材料归档；需要时可开具团员证明。"},
]

LEAGUE_TIMELINE = [
    {"stageKey": "l_apply", "durationDays": 14, "remindBeforeDays": 3, "material": "入团申请书、团课学习记录"},
    {"stageKey": "l_activist", "durationDays": 90, "remindBeforeDays": 14, "material": "培养考察表、志愿服务时长证明"},
    {"stageKey": "l_develop", "durationDays": 30, "remindBeforeDays": 7, "material": "评议材料、公示记录、审批表"},
    {"stageKey": "l_member", "durationDays": 0, "remindBeforeDays": 0, "material": "团员证、志愿书归档"},
]

CALENDAR_HIGHLIGHTS = [
    {"date": "2025-09-08", "title": "秋季学期开学", "note": "2025 级新生注册与入学教育", "partyHint": "新生团支部建立、入党/入团申请集中受理", "tags": ["校历", "党团", "迎新"]},
    {"date": "2025-10-01", "title": "国庆节假期", "note": "10 月 1 日至 8 日放假", "partyHint": "开展主题党日、团日活动与理论学习", "tags": ["校历", "党团", "组织生活"]},
    {"date": "2025-12-29", "title": "秋季学期考试周", "note": "12 月 29 日至 2026 年 1 月 9 日", "partyHint": "考试周前提交思想汇报；预备党员做好组织生活准备", "tags": ["校历", "党团", "思想汇报"]},
    {"date": "2026-01-12", "title": "寒假开始", "note": "学生 1 月 12 日起放寒假", "partyHint": "寒假社会实践与先锋计划动员", "tags": ["校历", "党团"]},
    {"date": "2026-03-02", "title": "春季学期开学", "note": "全体学生返校上课", "partyHint": "积极分子培养考察中期检查、发展对象材料收集启动", "tags": ["校历", "党团", "培养考察"]},
    {"date": "2026-04-05", "title": "清明节", "note": "4 月 5 日放假", "partyHint": "祭扫缅怀、主题党团日", "tags": ["校历", "党团", "组织生活"]},
    {"date": "2026-05-01", "title": "劳动节", "note": "5 月 1 日放假", "partyHint": "劳动教育实践、志愿服务", "tags": ["校历", "党团", "实践"]},
    {"date": "2026-06-19", "title": "端午节", "note": "6 月 19 日放假", "partyHint": "传统文化与爱国主义教育", "tags": ["校历", "党团"]},
    {"date": "2026-06-22", "title": "春季学期考试周", "note": "6 月 22 日至 7 月 3 日", "partyHint": "预备党员转正材料、发展对象政审与培训收尾", "tags": ["校历", "党团", "思想汇报"]},
    {"date": "2026-07-06", "title": "先锋社会实践", "note": "暑期社会实践与先锋计划（参考学院具体通知）", "partyHint": "入团积极分子志愿服务、入党积极分子实践锻炼", "tags": ["校历", "党团", "社会实践"]},
    {"date": "2026-07-13", "title": "暑假开始", "note": "学生 7 月 13 日起放暑假", "partyHint": "暑期社会实践、组织关系转接与档案整理", "tags": ["校历", "党团"]},
]

OFFICIAL_KNOWLEDGE = [
    (
        "k_party_flow",
        "发展党员工作程序（29 个环节）",
        "党团事务",
        ["入党", "发展党员", "流程", "29环节"],
        "依据官方流程图：5 大阶段、29 个环节，从教育引导到材料归档。",
        """## 总体说明

发展党员工作须按照「控制总量、优化结构、提高质量、发挥作用」的总要求，严格程序、严肃纪律。

## 五大阶段

1. **入党积极分子确定**（环节 1-5）：教育引导 → 接收申请书并谈话 → 确定积极分子备案 → 指定培养联系人 → 考察。
2. **发展对象确定**（环节 6-10）：支委会讨论 → 备案 → 确定介绍人 → 政治审查 → 短期集中培训。
3. **预备党员接收**（环节 11-19）：讨论 → 预审 → 公示 → 支部大会 → 报党委 → 谈话 → 审批 → 通知 → 备案。
4. **预备党员教育考察与转正**（环节 20-28）：编入支部 → 宣誓 → 考察 → 转正申请 → 公示 → 支部大会 → 报党委 → 审批 → 通知。
5. **正式党员**（环节 29）：材料存档。

## 在本平台如何使用

- 在「党团流程」页查看当前阶段对应的环节清单，按清单准备材料。
- 环节进度可由本人勾选完成，管理老师在「工作台」推进阶段并刷新提醒。
- 可下载《发展党员工作程序图》PNG 对照查看。

## 联系方式

信息学院党委组织工作咨询：010-62513007（以学院最新公布为准）。""",
        False,
        ["doc_flowchart"],
    ),
    (
        "k_party_calendar",
        "2025-2026 学年校历与党团活动安排",
        "党团事务",
        ["校历", "2025", "2026", "社会实践"],
        "中国人民大学 2025-2026 学年校历要点：开学、考试周、寒暑假与先锋社会实践时间。",
        """## 学年概览

- **秋季学期**：2025 年 9 月 8 日 — 2026 年 1 月 11 日
- **春季学期**：2026 年 3 月 2 日 — 2026 年 7 月 12 日

## 与党团工作相关的节点

| 时间 | 事项 |
| --- | --- |
| 9 月 | 新生入学教育、团支部建立、入党/入团申请集中受理期 |
| 10 月 | 国庆节；适合开展主题党日、团日活动 |
| 12 月-1 月 | 秋季考试周与寒假前思想汇报、组织生活会 |
| 3 月 | 春季学期开学；积极分子培养考察中期检查 |
| 4-5 月 | 春季运动会、劳动节；发展对象培训与政审材料收集 |
| 6-7 月 | 考试周、毕业典礼、**先锋社会实践**（约 7 月 6 日起） |

## 附件

平台提供校历 PNG 原图下载，请以学校办公室最新发布为准。""",
        False,
        ["doc_calendar"],
    ),
    (
        "k_party_cert",
        "党员证明与团员证明办理说明",
        "党团事务",
        ["党员证明", "团员证明", "模板"],
        "学院党委/团委开具组织关系证明的标准格式与填写要点。",
        """## 党员证明

适用于需证明**中共党员身份**、**入党时间**、**组织关系所在支部**等场景（如实习、出国、政审等）。

**填写要点：**
- 姓名、性别、学号、身份证号
- 年级专业（本科/硕士/博士）
- 入党时间（以支部大会通过预备党员之日为准）
- 组织关系所在党支部全称

**办理路径：** 向所在学生党支部或学院党委办公室申请 → 审核后开具 → 可下载 Word 模板预览格式。

## 团员证明

适用于需证明**共青团员身份**、**入团时间**、**团员编号**等场景。

**填写要点：**
- 姓名、学号、身份证号
- 班级
- 入团时间与团员编号

**办理路径：** 向团支部或学院团委申请 → 审核后开具。

## 模板下载

在「政策知识库 → 常用模板」或「党团流程 → 官方文件」中下载 Word 模板。""",
        False,
        ["doc_party_cert", "doc_league_cert"],
    ),
    (
        "k_party_activist",
        "入党积极分子培养考察材料清单",
        "党团事务",
        ["积极分子", "思想汇报", "培养考察"],
        "培养考察期不少于一年，需定期提交思想汇报并填写培养考察登记表。",
        """## 必备材料

1. 入团推优表（或同级推优材料）
2. 《入党积极分子培养考察登记表》
3. 思想汇报（一般每季度至少一篇）
4. 培养联系人考察意见
5. 党校或学院分党校培训结业证明（如有）

## 时间要求

- 培养考察时间**一般不少于一年**，从党委备案为积极分子之日算起。
- 平台会在培养期满前 30 天自动生成提醒任务。

## 思想汇报

可使用平台「常用模板 → 思想汇报模板」，结合个人学习、实践与党性修养实际撰写。""",
        False,
        [],
    ),
    (
        "k_party_probation",
        "预备党员接收、教育考察与转正（环节 11-28）",
        "党团事务",
        ["预备党员", "转正", "公示", "支部大会"],
        "依据官方流程图：接收预备党员须预审、公示、支部大会表决；预备期一年，期满转正须再次公示与审批。",
        """## 接收预备党员（环节 11-19）

- 支委会讨论并形成审查意见
- **党委预审**后，对拟接收对象**公示不少于五个工作日**
- **支部大会**讨论接收，有表决权到会人数须超过应到会半数
- 报党委审批，**三个月内**完成（特殊情况不超过六个月）

## 预备期教育考察（环节 20-22）

- 编入党支部和党小组，举行**入党宣誓**
- 预备期**一年**，从支部大会通过之日算起
- 填写预备党员考察表，继续提交思想汇报

## 转正（环节 23-28）

- 预备期满前提交**转正申请书**
- 再次**公示**并召开支部大会讨论
- 党委**三个月内**作出转正、延长预备期或取消资格的决定

## 官方依据

详见「发展党员工作程序图」及《中国共产党发展党员工作细则》。""",
        False,
        ["doc_flowchart"],
    ),
    (
        "k_party_league",
        "共青团员发展流程（8 环节）",
        "党团事务",
        ["入团", "共青团", "团员证明"],
        "入团申请 → 团课学习 → 积极分子培养 → 评议公示 → 上级审批 → 宣誓归档。",
        """## 四个阶段

1. **入团申请**：提交申请书，参加团课与青年大学习
2. **入团积极分子**：团支部培养考察，完成志愿服务时长（以公示为准）
3. **发展对象**：支委会评议、公示，报学院/校团委审批
4. **共青团员**：入团宣誓，团员证与志愿书归档

## 团员证明

需开具证明时，请对照官方「团员证明模板」填写学号、入团时间与团员编号，在「办事申请」提交。

## 与校历联动

暑期「先锋社会实践」（约 7 月 6 日）是入团积极分子实践锻炼的重要节点。""",
        False,
        ["doc_league_cert", "doc_calendar"],
    ),
]

OFFICIAL_TEMPLATES = [
    ("tpl_party_cert", "党员证明模板", "党团证明", "docx", "party_cert"),
    ("tpl_league_cert", "团员证明模板", "党团证明", "docx", "league_cert"),
    ("tpl_report", "思想汇报模板", "党团材料", "docx", None),
]

OFFICIAL_THEORY_QUESTIONS = [
    ("theory_off_01", "发展党员工作总要求包括控制总量、优化结构、提高质量、发挥作用。", "正确;错误", "正确", "这是发展党员工作的四项总要求。", "发展党员总则"),
    ("theory_off_02", "党组织收到入党申请书后，应当在一个月内派人同入党申请人谈话。", "正确;错误", "正确", "谈话应在收到申请书后一个月内完成。", "入党申请人"),
    ("theory_off_03", "入党积极分子培养考察时间一般不少于一年。", "正确;错误", "正确", "培养考察期通常不少于一年。", "积极分子"),
    ("theory_off_04", "发展对象应当有两名正式党员作入党介绍人。", "正确;错误", "正确", "介绍人一般应有两名正式党员。", "发展对象"),
    ("theory_off_05", "发展对象必须参加短期集中培训，时间一般不少于三天或二十四个学时。", "正确;错误", "正确", "集中培训是发展对象的必备环节。", "发展对象"),
    ("theory_off_06", "接收预备党员公示期一般不少于五个工作日。", "正确;错误", "正确", "公示期不少于五个工作日。", "预备党员接收"),
    ("theory_off_07", "预备党员的预备期为一年，从支部大会通过其为预备党员之日算起。", "正确;错误", "正确", "预备期一年，从支部大会通过之日算起。", "预备党员"),
    ("theory_off_08", "党委对预备党员转正、延长预备期或取消预备党员资格的审批，应当在三个月内完成。", "正确;错误", "正确", "审批应在三个月内完成。", "预备党员转正"),
    ("theory_off_09", "政治审查的主要对象是发展对象本人；对主要社会关系的审查，原则上不查其祖父母和外祖父母。", "正确;错误", "正确", "政审范围按细则规定把握。", "政治审查"),
    ("theory_off_10", "预备党员可以参加讨论本人转正的支部大会，并作为有表决权党员参与投票。", "正确;错误", "错误", "预备党员没有表决权、选举权和被选举权，转正讨论时本人可参加但不参与表决。", "预备党员"),
    ("theory_off_11", "发展党员工作程序共 29 个环节，分为 5 个阶段。", "正确;错误", "正确", "官方流程图标注为 5 阶段 29 环节。", "发展程序"),
    ("theory_off_12", "团员发展对象须经过团支部评议公示和上级团委审批。", "正确;错误", "正确", "入团程序需经团支部与上级团组织审批。", "共青团"),
    ("theory_off_13", "对拟接收为预备党员的对象，公示期一般不少于五个工作日。", "正确;错误", "正确", "官方流程图环节 13 明确要求。", "预备党员接收"),
    ("theory_off_14", "党委对预备党员转正作出决定的期限一般为三个月。", "正确;错误", "正确", "环节 27 与细则一致。", "预备党员转正"),
    ("theory_off_15", "入党积极分子思想汇报一般每季度至少提交一篇。", "正确;错误", "正确", "培养考察期材料要求。", "积极分子"),
    ("theory_off_16", "团员证明须填写入团时间与团员编号。", "正确;错误", "正确", "学院团委证明模板必填项。", "共青团"),
]


def _stage_macro_map() -> dict[str, str]:
    return {item["key"]: item.get("macroStage", item["name"]) for item in OFFICIAL_FLOW_STAGES}


def _league_stage_macro_map() -> dict[str, str]:
    return {item["key"]: item["name"] for item in LEAGUE_FLOW_STAGES}


def enrich_official_step(step: dict, *, league: bool = False) -> dict:
    macro_map = _league_stage_macro_map() if league else _stage_macro_map()
    payload = dict(step)
    payload["macroStage"] = macro_map.get(step["stageKey"], "")
    payload["timeRule"] = STEP_TIME_RULES.get(step["id"], "")
    payload["materialCatalog"] = STEP_MATERIALS_MAP.get(step["id"], [])
    return payload


def build_official_guide() -> dict:
    party_groups: dict[str, list] = {}
    for step in OFFICIAL_STEPS:
        enriched = enrich_official_step(step)
        party_groups.setdefault(enriched["macroStage"], []).append(enriched)
    league_groups: dict[str, list] = {}
    for step in LEAGUE_STEPS:
        enriched = enrich_official_step(step, league=True)
        league_groups.setdefault(enriched["macroStage"], []).append(enriched)
    return {
        "meta": OFFICIAL_META,
        "partyMacroGroups": [{"name": name, "steps": steps} for name, steps in party_groups.items()],
        "leagueMacroGroups": [{"name": name, "steps": steps} for name, steps in league_groups.items()],
        "certFields": CERT_FIELD_SPECS,
        "thoughtReportGuide": THOUGHT_REPORT_GUIDE,
        "calendarHighlights": CALENDAR_HIGHLIGHTS,
        "knowledgeTopics": [
            {"id": kid, "title": title, "tags": tags}
            for kid, title, _cat, tags, _sum, _body, _sens, _assets in OFFICIAL_KNOWLEDGE
        ],
        "officialAssets": [
            {"id": meta["id"], "key": key, "title": meta["title"], "description": meta["description"]}
            for key, meta in OFFICIAL_ASSETS.items()
        ],
    }
