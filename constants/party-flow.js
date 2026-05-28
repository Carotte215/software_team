/**
 * 党团阶段定义：管理端可改配置；学生端按 key 驱动时间线与提醒规则。
 * 与需求状态图节点名称对齐（可随甲方确认再改文案）。
 */
module.exports.DEFAULT_STAGES = [
  { key: 'applicant', name: '入党申请人', order: 1, desc: '接受教育引导，递交入党申请书，党组织派人谈话并留存记录' },
  { key: 'activist', name: '入党积极分子确定', order: 2, desc: '经团支部推优、支委会讨论并报党委备案，指定培养联系人，开展一年以上培养考察' },
  { key: 'candidate', name: '发展对象确定', order: 3, desc: '支委会听取意见后讨论，报党委备案；确定入党介绍人，完成政治审查与短期集中培训' },
  { key: 'probationary', name: '预备党员接收与转正', order: 4, desc: '党委预审、公示、支部大会接收预备党员；预备期内教育考察，期满提交转正申请并完成审批' },
  { key: 'member', name: '正式党员', order: 5, desc: '转正审批通过，材料归档，进入正式党员教育管理' },
];

module.exports.DEFAULT_RULES = [
  {
    id: 'r1',
    trigger: 'stage_enter',
    stageKey: 'activist',
    afterDays: 90,
    title: '积极分子培养期满前提醒',
    body: '请核对培养考察记录是否齐全，准备进入下一阶段评审材料。',
  },
  {
    id: 'r2',
    trigger: 'stage_enter',
    stageKey: 'probationary',
    afterDays: 300,
    title: '预备期满前提醒',
    body: '预备期满前请按支部安排提交转正申请书与相关材料。',
  },
];
