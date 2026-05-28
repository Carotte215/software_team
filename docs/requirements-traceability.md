# 需求追溯矩阵（V3.0 对照）

| 需求 | 实现 | 说明 |
| --- | --- | --- |
| FR1 知识库 | `knowledge.py` + `KnowledgeMissKeyword` | 检索、上下线、未命中词表、敏感摘要、官方链接、CSV 导出 |
| FR1-5 模板 | `files.py` + `templates.py` + `TemplateFile` | 分类展示、真实上传与下载；未上传真实模板文件时明确返回错误，不再生成占位下载 |
| FR2 党团 | `party.py` + `PartyStage`/`PartyTimelineRule` | 阶段入库/可配置、时间线、自动提醒、全员进度列表 |
| FR2-6/7 理论 | `theory.py` | 题库 CRUD/导入、随机抽题、判分记录、每日答题限次 |
| FR3 通知 | `notices.py` + `message_channels.py` | 定向规则、批次统计、站内信真实投递；当前互测版本默认只启用站内链路 |
| FR3-1 导入 | `POST /workbench/notices/import` | 外部通知录入 |
| FR3-2 URL 抓取 | `POST /workbench/notices/fetch-url` | HTML 正文简化提取入库 |
| FR4 审批 | `applications.py` + `application_templates.py` | 草稿/审批/48h 撤回、HTML 模板、PDF/预览、CSV 导出 |
| FR5 荣誉 | `honors.py` | 附件/可见性、筛选、删除、上下线（`online`） |
| FR6 画像 | `students.py` + Workbench 画像表单 | 字段策略、加密身份证（管理端录入/脱敏展示）、CSV/XLSX 导出、学生 extension 自维护 |
| FR7 学业 | `academic.py` + Workbench 方案表格 | PDF 表格/文本解析、可选 OCR、人工 confirm、缺口建议、培养方案模块表格维护 |
| NFR 认证/审计 | `auth.py`, `audit_logs`, `file_access.py` | JWT+密码、refresh、账号角色绑定、操作留痕、审计 CSV、附件业务鉴权 |
| NFR 健康/调度 | `health.py`, `scheduler.py` | DB ping、SMTP 状态、定时通知派发与党团提醒 |

**需求明确不做（Out of Scope）**：微信 OAuth、微哨对接、真实短信网关、开放对话 AI、正式电子签章、复杂选课引擎。

**部署前置**：Kingbase 切换 `DATABASE_URL`（见 `scripts/probe-kingbase.py`）；本地 `scripts/setup-local.ps1` 或 `pip install -r backend/requirements.txt` 后 `PYTHONPATH=backend python -m app.seed`。

**测试口径**：当前互测版本默认走真实后端；`web/src/api/mockGateway.js` 仅保留开发兼容，不作为主测试路径。
