from datetime import datetime, timedelta, timezone

FLOW_STAGES = [
    {"key": "applicant", "name": "入党申请人", "desc": "递交申请书，完成谈话记录。", "order": 1},
    {"key": "activist", "name": "入党积极分子", "desc": "培养教育不少于 1 年。", "order": 2},
    {"key": "candidate", "name": "发展对象", "desc": "政审、公示、集中培训。", "order": 3},
    {"key": "probationary", "name": "预备党员", "desc": "支部审批并进入预备期。", "order": 4},
    {"key": "member", "name": "正式党员", "desc": "转正审批通过。", "order": 5},
]

MODULES = [
    {"key": "gen_req", "name": "通识必修", "required": 12},
    {"key": "gen_ele", "name": "通识选修", "required": 8},
    {"key": "major_core", "name": "专业核心", "required": 28},
    {"key": "major_ele", "name": "专业选修", "required": 14},
    {"key": "practice", "name": "实践环节", "required": 8},
]

NOW = datetime.now(timezone.utc)

STUDENTS = [
    ("2024201581", "朱启哲", "2024级", "软件工程", "软工2401", "汉族", "13800001581", "共青团员", "张老师", "北京"),
    ("2023200444", "赵子涵", "2023级", "计算机科学与技术", "计科2302", "汉族", "13900004444", "入党积极分子", "李老师", "上海"),
    ("2022200999", "李煜南", "2022级", "信息安全", "信安2201", "回族", "13700009999", "中共预备党员", "王老师", "深圳"),
    ("2024210888", "钱晨", "2024级", "软件工程", "软工2402", "汉族", "13500008888", "共青团员", "张老师", "南京"),
]

KNOWLEDGE = [
    ("k_award", "奖助学金：资格、材料与时间线", "奖助政策", ["奖助学金", "贫困认定"], "以学院当年细则为准，困难认定需提交家庭经济信息采集表。", False),
    ("k_dorm", "宿舍调整：申请—审批—物业流转", "后勤事务", ["宿舍", "调整"], "向辅导员说明原因，经学院审批后进入物业调宿流程。", False),
    ("k_leave", "休学/复学：学籍规则与材料清单", "学籍事务", ["休学", "复学"], "按学校学籍管理规定提交申请与佐证材料。", False),
    ("k_party", "入党申请人与积极分子材料说明", "党团事务", ["入党", "积极分子"], "递交申请书后，团支部推优，支部安排谈话并留存记录。", False),
    ("k_cert", "在读证明：抬头、份数与英文版", "证明模板", ["在读证明", "英文证明"], "提交申请时写清抬头、份数、是否需要英文版。", False),
    ("k_seal", "盖章申请：附件必传与涉密转线下", "行政事务", ["盖章", "用印"], "盖章申请必须上传材料，涉密内容备注后转线下流转。", True),
]

TEMPLATES = [
    ("tpl_leave", "请假条（通用）", "日常请假", "docx"),
    ("tpl_budget", "学生活动经费预算表", "团学活动", "xlsx"),
    ("tpl_report", "思想汇报模板", "党团材料", "docx"),
]

NOTICES = [
    ("n_practice", "2026 春季社会实践项目申报", ["实践", "竞赛"], "面向本科与研究生开放申报，请按附件要求组队。", NOW - timedelta(days=2)),
    ("n_award", "奖助学金材料补交通知", ["奖助学金"], "尚未补齐材料的同学请在周五前补交扫描件。", NOW - timedelta(days=4)),
    ("n_party", "支部组织生活会安排", ["党团"], "本周五晚进行专题组织生活会，请提前准备发言提纲。", NOW - timedelta(hours=9)),
]

THEORY_QUESTIONS = [
    ("theory_q1", "入党申请人递交申请书后，通常应接受党组织的谈话和培养教育。", "正确;错误", "正确", "入党申请提交后，党组织会安排谈话并开展培养教育。", "入党流程"),
    ("theory_q2", "发展对象阶段通常需要完成政审、公示和集中培训等材料或环节。", "正确;错误", "正确", "发展对象阶段需按组织要求完成相关审查和培训材料。", "发展对象"),
    ("theory_q3", "预备党员的预备期为一年，从支部大会通过其为预备党员之日算起。", "正确;错误", "正确", "预备期一般为一年。", "预备党员"),
    ("theory_q4", "入党积极分子培养教育时间一般不少于一年。", "正确;错误", "正确", "积极分子培养考察期通常不少于一年。", "积极分子"),
    ("theory_q5", "团员推优是确定入党积极分子的重要途径之一。", "正确;错误", "正确", "团支部推优是常见程序。", "入党流程"),
    ("theory_q6", "发展对象可以不参加短期集中培训直接入党。", "正确;错误", "错误", "发展对象须参加集中培训并结业。", "发展对象"),
    ("theory_q7", "思想汇报应结合个人实际，定期向党组织汇报。", "正确;错误", "正确", "思想汇报是培养考察的重要材料。", "积极分子"),
    ("theory_q8", "正式党员享有表决权、选举权和被选举权。", "正确;错误", "正确", "这是党员的基本权利。", "正式党员"),
]

APPLICATION_TEMPLATES = [
    (
        "tpl_cert",
        "在读证明模板",
        "证明申请",
        "在读证明",
        """<!doctype html><html><head><meta charset="utf-8"/><title>在读证明</title>
<style>body{font-family:SimSun,serif;padding:40px}h1{text-align:center}p{line-height:2;font-size:16px}</style></head>
<body><h1>在读证明</h1>
<p>兹证明 {{name}}，学号 {{studentId}}，系我院 {{grade}} {{major}} 专业 {{className}} 班在读学生。</p>
<p>申请事由：{{reason}}</p>
<p>特此证明。</p>
<p style="text-align:right;margin-top:60px">学院学生工作办公室<br/>{{generatedAt}}</p></body></html>""",
    ),
    (
        "tpl_leave",
        "请假条模板",
        "请假申请",
        "",
        """<!doctype html><html><head><meta charset="utf-8"/><title>请假条</title></head>
<body style="font-family:SimSun,serif;padding:40px">
<h2 style="text-align:center">请假条</h2>
<p>姓名：{{name}}　学号：{{studentId}}　班级：{{className}}</p>
<p>请假事由：{{reason}}</p>
<p>请假时间：{{startDate}} 至 {{endDate}}</p>
<p>申请人签名：________　日期：{{generatedAt}}</p></body></html>""",
    ),
]
