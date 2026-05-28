# 需求追溯矩阵（V3.0 对照 · Web 版）

> 交付形态：**仅 Web 应用**（Vue 3 + FastAPI）。小程序代码保留但不维护。

| 需求 | 实现 | 说明 |
| --- | --- | --- |
| FR1 知识库 | `knowledge.py` + `knowledge_engagement.py` | 检索、上下线、未命中词、敏感摘要、官方链接、CSV 导出；**标准答案优先排序**；无结果返回 `searchMeta.hint`；收藏/最近/热门 |
| FR1-5 模板 | `files.py` + `templates.py` + `TemplateFile` | 分类展示、真实上传与下载；未上传时 409 |
| FR1-7 未命中词 | `workbench.py` + WorkbenchView | 老师/协同/领导可查看；老师可「转为知识」 |
| FR2 党团 | `party.py` + `party_official_data.py` | **官方文件全量结构化**：29 环节材料/时限、校历党团提示、证明模板字段、官方指南 API |
| FR2 官方指南 | `GET /party/official-guide` | 大阶段分组、证明填写要点、思想汇报指南、知识库主题索引 |
| FR2 校历联动 | `party_calendar_events` + `refresh_calendar_reminder_tasks` | 老师维护校历；刷新提醒时生成近 21 天校历待办 |
| FR2-6/7 理论 | `theory.py` | 题库 CRUD/导入、随机抽题、判分、每日限次 |
| FR3 通知 | `notices.py` + `message_channels.py` | 定向规则（含 `partyStage` / `leagueStage`）、批次统计与日期筛选、站内信；邮件/短信模拟 |
| FR3-1 导入 | `POST /workbench/notices/import` | 外部通知录入 |
| FR3-2 URL 抓取 | `POST /workbench/notices/fetch-url` | HTML 正文简化提取入库 |
| FR4 审批 | `applications.py` + `application_validation.py` + `application_form.py` | 草稿/审批/48h 撤回；党员/团员/请假/盖章校验；**身份证加密**；HTML→PDF |
| FR5 荣誉 | `honors.py` + HonorsView | 附件/可见性、年级/专业筛选、删除、上下线、CSV 批量导入 |
| FR6 画像 | `students.py` + ProfileView + Workbench | 字段策略、扩展字段自维护、CSV/XLSX 导入导出 |
| FR7 学业 | `academic.py` + AcademicView | PDF 解析、OCR 可选、培养方案维护、缺口建议；管理端跳转工作台风险名单 |
| M10 需求追溯 | `HelpView.vue` + `web/src/data/requirements.js` | Web 路由对照与验收入口 |
| NFR 认证/审计 | `auth.py`, `audit_logs`, `file_access.py` | JWT、生产禁演示口令、审计 CSV、附件鉴权 |
| NFR 健康/调度 | `health.py`, `scheduler.py` | DB ping、SMTP 状态、通知派发、党团+入团提醒（6h） |

**首页增强（Web）**：学生待办（审批中/党团任务/学业风险）；管理端 summary 卡片。

**明确不做（Out of Scope）**：微信 OAuth、小程序、微哨对接、真实短信网关、开放对话 AI、正式电子签章、复杂选课引擎。

**部署前置**：Kingbase 切换 `DATABASE_URL`（见 `scripts/probe-kingbase.py`）；本地 `pip install -r backend/requirements.txt` 后 `PYTHONPATH=backend python -m app.seed`。

**测试口径**：互测版本默认走真实后端 Remote 模式；`web/src/api/mockGateway.js` 仅保留开发兼容。

**测试账号**（密码 `Stu@` + 学号后 6 位）：2024201581 学生、2022200999 老师、2023200444 协同、2024210888 领导。
