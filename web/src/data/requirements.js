/** V3.0 需求模块索引（Web 验收追溯页） */
export const REQUIREMENT_MODULES = [
  {
    id: "M1",
    name: "智能问答与政策知识库",
    priority: "P0",
    items: [
      { fr: "FR1-1~6", desc: "政策维护、关键词检索、标准答案优先、敏感摘要、模板分类", route: "knowledge" },
      { fr: "FR1-7", desc: "高频未命中词统计与转知识", route: "workbench" },
      { fr: "扩展·收藏/最近/热门", desc: "收藏、最近浏览、热门政策", route: "knowledge" },
    ],
  },
  {
    id: "M2",
    name: "党团事务流程管理",
    priority: "P0",
    items: [
      { fr: "FR2-1~5", desc: "入党/入团阶段、29 环节、材料上传、思想汇报、校历要点", route: "party" },
      { fr: "FR2-6~7", desc: "理论自测题库、每日限次、随机抽题判分", route: "party" },
      { fr: "工作台·党团", desc: "阶段推进、环节确认、校历维护、提醒刷新", route: "workbench" },
    ],
  },
  {
    id: "M3",
    name: "信息集成与精准推送",
    priority: "P1",
    items: [
      { fr: "FR3-1~7", desc: "通知录入/URL 抓取、标签、定向规则（含党团阶段）、批次统计", route: "notices" },
    ],
  },
  {
    id: "M4",
    name: "电子证明与审批",
    priority: "P0",
    items: [
      { fr: "FR4-1~12", desc: "证明/请假/盖章、党员团员字段校验、预览 PDF、审批撤回", route: "apply" },
    ],
  },
  {
    id: "M5",
    name: "奖励荣誉展示",
    priority: "P1",
    items: [{ fr: "FR5-1~4", desc: "荣誉维护、年级/专业筛选、附件可见性、CSV 导入", route: "honors" }],
  },
  {
    id: "M6",
    name: "学生画像",
    priority: "P1",
    items: [
      { fr: "FR6-1~5", desc: "基础/扩展画像、字段权限、身份证加密、批量导入导出", route: "profile" },
    ],
  },
  {
    id: "M7",
    name: "学业分析与预警",
    priority: "P2",
    items: [{ fr: "FR7-1~7", desc: "培养方案、成绩单解析、缺口与建议、管理端风险名单", route: "academic" }],
  },
  {
    id: "M9",
    name: "管理端 / 领导视图",
    priority: "—",
    items: [
      { fr: "权限矩阵", desc: "四级角色、协同不可审批、可查看未命中词", route: "workbench" },
      { fr: "领导看板", desc: "运行概览、党团统计、学业风险", route: "workbench" },
    ],
  },
  {
    id: "M10",
    name: "工程元数据",
    priority: "—",
    items: [{ fr: "需求追溯", desc: "本页：模块—功能点—Web 路由对照，支持一键跳转", route: "help" }],
  },
];

export const OUT_OF_SCOPE = [
  "微信 OAuth / 小程序（本项目仅 Web 版）",
  "微哨对接、真实短信网关",
  "开放式大模型自由问答",
  "正式电子签章法律效力",
  "复杂选课引擎",
];
