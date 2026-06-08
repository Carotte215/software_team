<script setup>
import { computed, inject, onMounted, reactive, ref } from "vue";
import WorkbenchBatchTable from "../components/WorkbenchBatchTable.vue";
import { APPROVAL, FLOW_STAGES, ROLES } from "../data/seed.js";
import { formatTime } from "../utils.js";

const api = inject("api");
const session = inject("session");
const toast = inject("toast");

const summary = ref(null);
const applications = ref([]);
const batches = ref([]);
const logs = ref([]);
const leader = ref(null);
const misses = ref([]);
const sms = ref([]);
const selectedApplication = ref(null);
const knowledgeItems = ref([]);
const students = ref([]);
const honors = ref([]);
const academicRisks = ref([]);
const academicPlans = ref([]);
const partyTimeline = ref(null);
const partyProgressList = ref([]);
const leagueProgressList = ref([]);
const fieldPolicy = ref(null);
const studentImportFile = ref(null);
const studentImportOverwrite = ref(false);
const studentImportResult = ref(null);
const academicPlanImportFile = ref(null);
const academicPlanImportResult = ref(null);
const theoryQuestions = ref([]);
const theoryImportFile = ref(null);
const theoryImportResult = ref(null);
const workbenchTemplates = ref([]);
const appTemplates = ref([]);
const templateFile = ref(null);
const noticeImportForm = reactive({ title: "", summary: "", content: "", tags: "通知", source: "外部导入" });
const noticeUrlForm = reactive({ url: "", source: "网页抓取" });
const templateForm = reactive({ id: "", name: "", scene: "", format: "docx", fileId: "" });
const appTemplateForm = reactive({ id: "", name: "", applyType: "证明申请", subtype: "", bodyHtml: "" });
const academicPlanForm = reactive({
  grade: "",
  major: "",
  modules: [],
});
const studentForm = reactive({
  studentId: "",
  name: "",
  grade: "",
  major: "",
  className: "",
  nation: "",
  phone: "",
  politicalStatus: "",
  tutor: "",
  hometown: "",
  idCardMasked: "",
  idCard: "",
  extensionText: "{}",
});
const noticeForm = reactive({
  title: "",
  summary: "",
  content: "",
  tags: "通知,党团",
  kind: "all",
  value: "",
  extKey: "",
  extValue: "",
  scheduledAt: "",
  enableEmail: false,
  enableSmsSim: false,
});
const batchFilter = reactive({
  title: "",
  batchId: "",
  status: "",
  fromDate: "",
  toDate: "",
});
const calendarEvents = ref([]);
const knowledgeForm = reactive({
  id: "",
  title: "",
  category: "常见问题",
  tags: "",
  summary: "",
  body: "",
  officialLink: "",
  sensitiveHint: false,
  online: true,
  attachments: [],
});
const partyForm = reactive({
  studentId: "",
  nextKey: "activist",
  remark: "",
  force: false,
});
const leagueForm = reactive({
  studentId: "",
  nextKey: "l_activist",
  remark: "",
  force: false,
});
const honorForm = reactive({
  id: "",
  title: "",
  winner: "",
  year: new Date().getFullYear(),
  major: "",
  grade: "",
  category: "校级",
  intro: "",
  visibility: "public",
  attachments: [],
});
const theoryForm = reactive({
  id: "",
  stem: "",
  optionsText: "正确;错误",
  answer: "正确",
  explanation: "",
  category: "理论知识",
  online: true,
});

const WORKBENCH_PANELS = [
  { id: "overview", label: "总览看板", desc: "关键指标与领导看板", roles: [ROLES.TEACHER, ROLES.COORDINATOR, ROLES.LEADER] },
  { id: "approvals", label: "审批通知", desc: "申请审批、通知发布、批次追踪", roles: [ROLES.TEACHER, ROLES.COORDINATOR, ROLES.LEADER] },
  { id: "party", label: "党团管理", desc: "党团推进、校历、题库与进度台账", roles: [ROLES.TEACHER, ROLES.LEADER] },
  { id: "students", label: "学生画像", desc: "学生档案、导入导出与字段维护", roles: [ROLES.TEACHER, ROLES.COORDINATOR] },
  { id: "academic", label: "学业培养", desc: "学业风险与培养方案维护", roles: [ROLES.TEACHER, ROLES.LEADER] },
  { id: "honors", label: "荣誉展示", desc: "荣誉条目、证明材料与展示状态", roles: [ROLES.TEACHER, ROLES.COORDINATOR, ROLES.LEADER] },
  { id: "knowledge", label: "知识模板", desc: "知识库、未命中词与模板维护", roles: [ROLES.TEACHER, ROLES.COORDINATOR, ROLES.LEADER] },
  { id: "audit", label: "审计日志", desc: "操作记录与导出", roles: [ROLES.TEACHER, ROLES.COORDINATOR, ROLES.LEADER] },
];
const workbenchPanel = ref("overview");
const visibleWorkbenchPanels = computed(() => WORKBENCH_PANELS.filter((item) => item.roles.includes(session.value.role)));
const activeWorkbenchPanel = computed(() => {
  if (visibleWorkbenchPanels.value.some((item) => item.id === workbenchPanel.value)) {
    return workbenchPanel.value;
  }
  return visibleWorkbenchPanels.value[0]?.id || "overview";
});

function showWorkbenchPanel(id) {
  return activeWorkbenchPanel.value === id;
}

onMounted(load);

async function withActionError(action, fallbackMessage) {
  try {
    return await action();
  } catch (error) {
    toast(error.message || fallbackMessage);
    return null;
  }
}

async function load() {
  if (session.value.role === ROLES.STUDENT) return;
  summary.value = await api.getWorkbenchSummary();
  applications.value = (await api.listApplications({ scope: "workbench" }).catch(() => ({ list: [] }))).list || [];
  batches.value = (await api.listWorkbenchBatches(batchQuery()).catch(() => ({ list: [] }))).list || [];
  misses.value = (await api.listKnowledgeMisses().catch(() => ({ list: [] }))).list || [];
  sms.value = (await api.listSmsSimulations().catch(() => ({ list: [] }))).list || [];
  knowledgeItems.value = (await api.listKnowledgeAdmin().catch(() => ({ list: [] }))).list || [];
  students.value = (await api.listStudents().catch(() => ({ list: [] }))).list || [];
  fieldPolicy.value = await api.getStudentFieldPolicy().catch(() => null);
  honors.value = (await api.listHonors(
    session.value.role === ROLES.TEACHER ? { include_offline: true } : {},
  ).catch(() => ({ list: [] }))).list || [];
  academicRisks.value = (await api.listAcademicRisks().catch(() => ({ list: [] }))).list || [];
  academicPlans.value = (await api.listAcademicPlans().catch(() => ({ list: [] }))).list || [];
  theoryQuestions.value = (await api.listTheoryQuestionAdmin().catch(() => ({ list: [] }))).list || [];
  partyTimeline.value = await api.getPartyTimeline().catch(() => null);
  partyProgressList.value = (await api.listPartyProgress(
    partyClassFilter.value ? { className: partyClassFilter.value } : {},
  ).catch(() => ({ list: [] }))).list || [];
  leagueProgressList.value = (await api.listLeagueProgress().catch(() => ({ list: [] }))).list || [];
  workbenchTemplates.value = (await api.listWorkbenchTemplates().catch(() => ({ list: [] }))).list || [];
  appTemplates.value = (await api.listApplicationTemplates().catch(() => ({ list: [] }))).list || [];
  if (!partyForm.studentId && students.value.length) partyForm.studentId = students.value[0].studentId;
  if (!leagueForm.studentId && students.value.length) leagueForm.studentId = students.value[0].studentId;
  await loadPartyPendingSteps();
  await loadLeaguePendingSteps();
  logs.value = (await api.listAuditLogs({ limit: 20 }).catch(() => ({ list: [] }))).list || [];
  leader.value = session.value.role === ROLES.LEADER
    ? await api.getLeaderDashboard().catch(() => null)
    : null;
  if ([ROLES.TEACHER, ROLES.LEADER].includes(session.value.role)) {
    calendarEvents.value = (await api.listPartyCalendarAdmin().catch(() => ({ list: [] }))).list || [];
  }
}

async function importExternalNotice() {
  if (!noticeImportForm.title.trim()) {
    toast("请填写通知标题");
    return;
  }
  const result = await withActionError(() => api.importNotice({
    title: noticeImportForm.title,
    summary: noticeImportForm.summary,
    content: noticeImportForm.content,
    tags: noticeImportForm.tags.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    source: noticeImportForm.source,
  }), "外部通知录入失败");
  if (!result) return;
  toast("外部通知已录入");
  Object.assign(noticeImportForm, { title: "", summary: "", content: "", tags: "通知", source: "外部导入" });
  await load();
}

async function fetchNoticeFromUrl() {
  if (!noticeUrlForm.url.trim()) {
    toast("请填写 URL");
    return;
  }
  const result = await withActionError(() => api.fetchNoticeUrl({ url: noticeUrlForm.url, source: noticeUrlForm.source }), "网页通知抓取失败");
  if (!result) return;
  toast("网页通知已抓取并入库");
  Object.assign(noticeUrlForm, { url: "", source: "网页抓取" });
  await load();
}

async function saveWorkbenchTemplate() {
  if (!templateForm.name.trim()) {
    toast("请填写模板名称");
    return;
  }
  if (!templateForm.id && !templateFile.value) {
    toast("新建模板时请先上传真实模板文件");
    return;
  }
  let fileId = templateForm.fileId;
  if (templateFile.value) {
    const uploaded = await withActionError(() => api.uploadFile(templateFile.value, "template"), "模板文件上传失败");
    if (!uploaded) return;
    fileId = uploaded.id;
  }
  const payload = {
    name: templateForm.name,
    scene: templateForm.scene,
    format: templateForm.format,
    fileId,
  };
  if (templateForm.id) {
    const result = await withActionError(() => api.updateWorkbenchTemplate(templateForm.id, payload), "模板更新失败");
    if (!result) return;
    toast("模板已更新");
  } else {
    const result = await withActionError(() => api.createWorkbenchTemplate(payload), "模板创建失败");
    if (!result) return;
    toast("模板已创建");
  }
  Object.assign(templateForm, { id: "", name: "", scene: "", format: "docx", fileId: "" });
  templateFile.value = null;
  await load();
}

async function editWorkbenchTemplate(item) {
  Object.assign(templateForm, {
    id: item.id,
    name: item.name,
    scene: item.scene || "",
    format: item.format || "docx",
    fileId: item.fileId || "",
  });
}

async function deleteWorkbenchTemplate(id) {
  if (!window.confirm("确认删除该模板？")) return;
  const result = await withActionError(() => api.deleteWorkbenchTemplate(id), "模板删除失败");
  if (!result) return;
  toast("模板已删除");
  await load();
}

function editAppTemplate(item) {
  Object.assign(appTemplateForm, {
    id: item.id,
    name: item.name,
    applyType: item.applyType || "",
    subtype: item.subtype || "",
    bodyHtml: item.bodyHtml || "",
  });
}

async function saveAppTemplate() {
  if (!appTemplateForm.name.trim()) {
    toast("请填写模板名称");
    return;
  }
  if (!appTemplateForm.bodyHtml.trim()) {
    toast("请填写申请模板 HTML 内容");
    return;
  }
  const payload = { ...appTemplateForm };
  if (appTemplateForm.id) {
    const result = await withActionError(() => api.updateApplicationTemplate(appTemplateForm.id, payload), "申请模板更新失败");
    if (!result) return;
    toast("申请模板已更新");
  } else {
    const result = await withActionError(() => api.createApplicationTemplate(payload), "申请模板创建失败");
    if (!result) return;
    toast("申请模板已创建");
  }
  Object.assign(appTemplateForm, { id: "", name: "", applyType: "证明申请", subtype: "", bodyHtml: "" });
  await load();
}

async function deleteAppTemplate(id) {
  if (!window.confirm("确认删除该申请模板？")) return;
  const result = await withActionError(() => api.deleteApplicationTemplate(id), "申请模板删除失败");
  if (!result) return;
  toast("申请模板已删除");
  await load();
}

async function publishNotice() {
  if (!noticeForm.title.trim() || !noticeForm.summary.trim() || !noticeForm.content.trim()) {
    toast("请填写通知标题、摘要和正文");
    return;
  }
  if (noticeForm.kind !== "all" && !String(noticeForm.value || "").trim()) {
    toast("当前定向规则需要填写匹配值");
    return;
  }
  if (noticeForm.kind === "extension" && (!noticeForm.extKey.trim() || !noticeForm.extValue.trim())) {
    toast("扩展字段定向需要填写扩展键和值");
    return;
  }
  const tags = noticeForm.tags.split(/[,，]/).map((item) => item.trim()).filter(Boolean);
  const targetRule = { kind: noticeForm.kind, value: noticeForm.value };
  if (noticeForm.kind === "extension") {
    targetRule.extKey = noticeForm.extKey;
    targetRule.extValue = noticeForm.extValue;
  }
  const result = await withActionError(() => api.publishNotice({
    title: noticeForm.title,
    summary: noticeForm.summary,
    content: noticeForm.content,
    tags,
    targetRule,
    scheduledAt: noticeForm.scheduledAt ? new Date(noticeForm.scheduledAt).getTime() : 0,
    enableEmail: noticeForm.enableEmail,
    enableSmsSim: noticeForm.enableSmsSim,
  }), "通知发布失败");
  if (!result) return;
  toast(result.scheduled ? "已生成定时通知批次" : "已生成通知批次");
  Object.assign(noticeForm, {
    title: "", summary: "", content: "", tags: "通知,党团", kind: "all", value: "",
    extKey: "", extValue: "", scheduledAt: "", enableEmail: false, enableSmsSim: false,
  });
  await load();
}

function batchQuery() {
  const query = {
    title: batchFilter.title,
    batchId: batchFilter.batchId,
    status: batchFilter.status,
  };
  if (batchFilter.fromDate) query.fromMs = new Date(batchFilter.fromDate).getTime();
  if (batchFilter.toDate) query.toMs = new Date(`${batchFilter.toDate}T23:59:59`).getTime();
  return query;
}

async function saveCalendarEvents() {
  const result = await withActionError(
    () => api.savePartyCalendarAdmin(calendarEvents.value),
    "校历保存失败",
  );
  if (!result) return;
  toast(`已保存 ${result.count || calendarEvents.value.length} 条校历事件`);
  await load();
}

function addCalendarRow() {
  calendarEvents.value.push({
    id: `cal_${Date.now()}`,
    date: "",
    title: "",
    note: "",
    online: true,
  });
}

async function applyBatchFilter() {
  batches.value = (await api.listWorkbenchBatches(batchQuery()).catch(() => ({ list: [] }))).list || [];
}

async function dispatchScheduled() {
  const result = await withActionError(() => api.dispatchScheduledNotices(), "定时通知派发失败");
  if (!result) return;
  toast(`已派发 ${result.dispatched} 个到期批次`);
  await load();
}

async function decide(id, action) {
  if (["revoke", "reapprove"].includes(action) && !window.confirm("确认执行该高风险审批操作？将写入审计日志。")) {
    return;
  }
  const message = action === "reject" ? "驳回原因" : "审批意见";
  const text = window.prompt(message, action === "reject" ? "材料不全，请补充后重提。" : "同意。") || "";
  const payload = action === "reject" ? { reason: text } : { comment: text };
  const result = await withActionError(() => api.decideApplication(id, action, payload), "审批操作失败");
  if (!result) return;
  toast("操作完成");
  selectedApplication.value = null;
  await load();
}

async function openApplication(item) {
  selectedApplication.value = await api.getApplication(item.id).catch(() => item);
}

function decisionButtons(item) {
  if (item.status === APPROVAL.PENDING) return ["approve", "reject"];
  if ([APPROVAL.APPROVED, APPROVAL.REJECTED].includes(item.status)) return ["revoke", "reapprove"];
  return [];
}

function decisionLabel(action) {
  return { approve: "通过", reject: "驳回", revoke: "撤回", reapprove: "重批" }[action] || action;
}

function resetKnowledgeForm() {
  Object.assign(knowledgeForm, {
    id: "",
    title: "",
    category: "常见问题",
    tags: "",
    summary: "",
    body: "",
    officialLink: "",
    sensitiveHint: false,
    online: true,
    attachments: [],
  });
}

function editKnowledge(item) {
  Object.assign(knowledgeForm, {
    id: item.id,
    title: item.title,
    category: item.category,
    tags: (item.tags || []).join(","),
    summary: item.summary,
    body: item.body || "",
    officialLink: item.officialLink || "",
    sensitiveHint: Boolean(item.sensitiveHint),
    online: item.online !== false,
    attachments: item.attachments || [],
  });
}

function fillFromMiss(item) {
  Object.assign(knowledgeForm, {
    id: "",
    title: item.keyword,
    category: "常见问题",
    tags: item.keyword,
    summary: `关于“${item.keyword}”的标准答复待补充。`,
    body: "",
    sensitiveHint: false,
    online: false,
    attachments: [],
  });
}

function onKnowledgeFiles(event) {
  knowledgeForm.attachments = [...knowledgeForm.attachments, ...Array.from(event.target.files || [])];
}

function isNativeFile(item) {
  return typeof File !== "undefined" && item instanceof File;
}

async function uploadKnowledgeAttachments() {
  return Promise.all(knowledgeForm.attachments.map(async (item) => (isNativeFile(item) ? api.uploadFile(item, "knowledge") : item)));
}

function knowledgePayload() {
  return {
    title: knowledgeForm.title,
    category: knowledgeForm.category,
    tags: knowledgeForm.tags.split(/[,，]/).map((item) => item.trim()).filter(Boolean),
    summary: knowledgeForm.summary,
    body: knowledgeForm.body,
    officialLink: knowledgeForm.officialLink,
    sensitiveHint: knowledgeForm.sensitiveHint,
    attachments: knowledgeForm.attachments,
    online: knowledgeForm.online,
  };
}

function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

async function saveKnowledge() {
  if (!knowledgeForm.title.trim() || !knowledgeForm.summary.trim()) {
    toast("请填写知识条目标题和摘要");
    return;
  }
  if (!knowledgeForm.body.trim() && !knowledgeForm.officialLink.trim()) {
    toast("请至少填写正文或官方链接");
    return;
  }
  const uploaded = await withActionError(() => uploadKnowledgeAttachments(), "知识附件上传失败");
  if (!uploaded) return;
  knowledgeForm.attachments = uploaded;
  if (knowledgeForm.id) {
    const result = await withActionError(() => api.updateKnowledge(knowledgeForm.id, knowledgePayload()), "知识条目更新失败");
    if (!result) return;
    toast("知识条目已更新");
  } else {
    const result = await withActionError(() => api.createKnowledge(knowledgePayload()), "知识条目创建失败");
    if (!result) return;
    toast("知识条目已创建");
  }
  resetKnowledgeForm();
  await load();
}

async function toggleKnowledge(item) {
  const result = await withActionError(() => api.setKnowledgeOnline(item.id, item.online === false), "知识条目状态更新失败");
  if (!result) return;
  toast(item.online === false ? "已上线" : "已下线");
  await load();
}

async function advanceParty() {
  if (!partyForm.studentId || !partyForm.nextKey) {
    toast("请选择学生和目标阶段");
    return;
  }
  const result = await withActionError(() => api.advancePartyStage({ ...partyForm }), "党团阶段推进失败");
  if (!result) return;
  toast("党团阶段已推进");
  partyForm.remark = "";
  await load();
}

async function advanceLeague() {
  if (!leagueForm.studentId || !leagueForm.nextKey) {
    toast("请选择学生和目标阶段");
    return;
  }
  const result = await withActionError(() => api.advanceLeagueStage({ ...leagueForm }), "入团阶段推进失败");
  if (!result) return;
  toast("入团阶段已推进");
  leagueForm.remark = "";
  await load();
}

const partyPendingSteps = ref([]);
const leaguePendingSteps = ref([]);
const partyClassFilter = ref("");
const partyStudentDetail = ref(null);

async function loadPartyPendingSteps() {
  if (!partyForm.studentId || session.value.role !== ROLES.TEACHER) {
    partyPendingSteps.value = [];
    partyStudentDetail.value = null;
    return;
  }
  const result = await api.getStudentPartyPendingSteps(partyForm.studentId).catch(() => ({ steps: [] }));
  partyPendingSteps.value = result.steps || [];
  partyStudentDetail.value = result;
}

async function loadLeaguePendingSteps() {
  if (!leagueForm.studentId || session.value.role !== ROLES.TEACHER) {
    leaguePendingSteps.value = [];
    return;
  }
  const result = await api.getStudentLeaguePendingSteps(leagueForm.studentId).catch(() => ({ steps: [] }));
  leaguePendingSteps.value = result.steps || [];
}

async function exportPartyProgress() {
  try {
    const blob = await api.exportPartyProgress();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "党团进度台账.csv";
    link.click();
    URL.revokeObjectURL(url);
    toast("党团台账已导出");
  } catch (error) {
    toast(error.message || "导出失败");
  }
}

async function downloadStepMaterial(file) {
  if (!file?.id && !file?.fileId && !file?.url) {
    toast("该环节附件缺少文件标识，无法下载");
    return;
  }
  try {
    const blob = await api.downloadFile(file);
    saveBlob(blob, file.name || "党团环节附件");
    toast("附件下载已开始");
  } catch (error) {
    toast(error.message || "附件下载失败");
  }
}

async function verifyPartyStep(studentId, stepId) {
  const result = await withActionError(
    () => api.verifyPartyStep({ studentId, stepId }),
    "环节确认失败",
  );
  if (!result) return;
  toast("环节已确认");
  await load();
  await loadPartyPendingSteps();
}

async function verifyLeagueStep(studentId, stepId) {
  const result = await withActionError(
    () => api.verifyLeagueStep({ studentId, stepId }),
    "入团环节确认失败",
  );
  if (!result) return;
  toast("入团环节已确认");
  await load();
  await loadLeaguePendingSteps();
}

async function refreshLeagueReminders() {
  const result = await withActionError(() => api.refreshLeagueReminders(), "入团提醒刷新失败");
  if (!result) return;
  toast(`已刷新 ${result.changed} 名学生的入团提醒`);
  await load();
}

const LEAGUE_STAGES = [
  { key: "l_apply", name: "入团申请" },
  { key: "l_activist", name: "入团积极分子" },
  { key: "l_develop", name: "发展对象" },
  { key: "l_member", name: "共青团员" },
];

function stageName(key) {
  const fromApi = partyTimeline.value?.stages?.find((stage) => stage.key === key);
  if (fromApi) return fromApi.name;
  return FLOW_STAGES.find((stage) => stage.key === key)?.name || key;
}

async function savePartyTimeline() {
  if (!partyTimeline.value?.rules?.length) {
    toast("暂无可保存的时间线规则");
    return;
  }
  const result = await withActionError(() => api.updatePartyTimeline(partyTimeline.value.rules), "党团时间线保存失败");
  if (!result) return;
  partyTimeline.value = result;
  toast("党团标准时间线已保存");
}

async function refreshPartyReminders() {
  const result = await withActionError(() => api.refreshPartyReminders(), "党团提醒刷新失败");
  if (!result) return;
  toast(`已刷新 ${result.changed} 名学生的提醒任务`);
  await load();
}

async function exportStudents(format = "csv") {
  try {
    const blob = await api.exportStudents(format);
    saveBlob(blob, format === "xlsx" ? "学生画像导出.xlsx" : "学生画像导出.csv");
    toast("学生画像导出已开始");
  } catch (error) {
    toast(error.message || "学生画像导出失败");
  }
}

async function exportKnowledgeCsv() {
  try {
    const blob = await api.exportKnowledge();
    saveBlob(blob, "知识库导出.csv");
    toast("知识库导出已开始");
  } catch (error) {
    toast(error.message || "知识库导出失败");
  }
}

async function exportApplicationsCsv() {
  try {
    const blob = await api.exportApplications();
    saveBlob(blob, "申请记录导出.csv");
    toast("申请记录导出已开始");
  } catch (error) {
    toast(error.message || "申请记录导出失败");
  }
}

async function exportAuditLogsCsv() {
  try {
    const blob = await api.exportAuditLogs();
    saveBlob(blob, "审计日志导出.csv");
    toast("审计日志导出已开始");
  } catch (error) {
    toast(error.message || "审计日志导出失败");
  }
}

async function savePartyStages() {
  if (!partyTimeline.value?.stages?.length) {
    toast("暂无阶段配置");
    return;
  }
  const result = await withActionError(() => api.updatePartyStages(partyTimeline.value.stages), "党团阶段配置保存失败");
  if (!result) return;
  toast("党团阶段名称与说明已保存");
  await load();
}

async function deleteHonor(id) {
  if (!window.confirm("确认删除该荣誉条目？")) return;
  const result = await withActionError(() => api.deleteHonor(id), "荣誉删除失败");
  if (!result) return;
  toast("荣誉条目已删除");
  await load();
}

async function toggleHonorOnline(item) {
  const result = await withActionError(() => api.setHonorOnline(item.id, !item.online), "荣誉状态更新失败");
  if (!result) return;
  toast(item.online ? "荣誉已下线" : "荣誉已上线");
  await load();
}

async function resetStudentPassword() {
  const studentId = window.prompt("输入要重置密码的学号");
  if (!studentId) return;
  const newPassword = window.prompt("输入新密码（至少 6 位）");
  if (!newPassword || newPassword.length < 6) {
    toast("密码过短");
    return;
  }
  const result = await withActionError(() => api.resetPassword({ studentId, newPassword }), "密码重置失败");
  if (!result) return;
  toast("密码已重置");
}

function canEditStudentField(field) {
  return Boolean(fieldPolicy.value?.editable?.includes(field));
}

function editStudent(item) {
  Object.assign(studentForm, {
    studentId: item.studentId,
    name: item.name || "",
    grade: item.grade || "",
    major: item.major || "",
    className: item.className || "",
    nation: item.nation || "",
    phone: item.phone || "",
    politicalStatus: item.politicalStatus || "",
    tutor: item.tutor || "",
    hometown: item.hometown || "",
    idCardMasked: item.idCardMasked || "",
    idCard: "",
    extensionText: JSON.stringify(item.extension || {}, null, 2),
  });
}

async function saveStudentProfile() {
  if (!studentForm.studentId) {
    toast("请选择学生");
    return;
  }
  let extension = {};
  try {
    extension = JSON.parse(studentForm.extensionText || "{}");
  } catch (error) {
    toast("扩展画像必须是 JSON 对象");
    return;
  }
  const payload = {};
  ["name", "grade", "major", "className", "nation", "phone", "politicalStatus", "tutor", "hometown"].forEach((field) => {
    if (canEditStudentField(field)) payload[field] = studentForm[field];
  });
  if (canEditStudentField("extension")) payload.extension = extension;
  if (canEditStudentField("idCard") && studentForm.idCard.trim()) payload.idCard = studentForm.idCard.trim();
  if (payload.phone && !/^[0-9-]{6,20}$/.test(payload.phone)) {
    toast("手机号格式不正确");
    return;
  }
  const result = await withActionError(() => api.updateStudent(studentForm.studentId, payload), "学生画像更新失败");
  if (!result) return;
  toast("学生画像已更新");
  await load();
}

function onStudentImportFile(event) {
  studentImportFile.value = event.target.files?.[0] || null;
  studentImportResult.value = null;
}

async function previewStudentImport() {
  if (!studentImportFile.value) {
    toast("请选择 CSV 或 XLSX 文件");
    return;
  }
  studentImportResult.value = await api.importStudents(studentImportFile.value, {
    dryRun: true,
    overwrite: studentImportOverwrite.value,
  }).catch((error) => ({ ok: false, errors: [{ row: 0, field: "file", message: error.message || "导入预检失败" }] }));
  toast(studentImportResult.value.errors?.length ? "导入预检发现错误" : "导入预检通过");
}

async function commitStudentImport() {
  if (!studentImportFile.value) {
    toast("请选择 CSV 或 XLSX 文件");
    return;
  }
  if (!window.confirm("确认写入学生数据？覆盖模式下将更新已有学号。")) {
    return;
  }
  studentImportResult.value = await api.importStudents(studentImportFile.value, {
    dryRun: false,
    overwrite: studentImportOverwrite.value,
  }).catch((error) => ({ ok: false, errors: [{ row: 0, field: "file", message: error.message || "导入失败" }] }));
  toast(studentImportResult.value.ok ? "学生数据已导入" : "导入失败，请先处理错误行");
  if (studentImportResult.value.ok) await load();
}

function resetHonorForm() {
  Object.assign(honorForm, {
    id: "",
    title: "",
    winner: "",
    year: new Date().getFullYear(),
    major: "",
    grade: "",
    category: "校级",
    intro: "",
    visibility: "public",
    attachments: [],
  });
}

function editHonor(item) {
  Object.assign(honorForm, { ...item, attachments: item.attachments || [], visibility: item.visibility || "public" });
}

function onHonorFiles(event) {
  honorForm.attachments = [...honorForm.attachments, ...Array.from(event.target.files || [])];
}

async function uploadHonorAttachments() {
  return Promise.all(
    honorForm.attachments.map(async (item) => {
      const file = isNativeFile(item) ? await api.uploadFile(item, "honor") : item;
      return { ...file, visibility: honorForm.visibility };
    }),
  );
}

function riskClass(level) {
  if (level === "高") return "orange";
  if (level === "低") return "green";
  return "gray";
}

function editAcademicPlan(item) {
  Object.assign(academicPlanForm, {
    grade: item.grade || "",
    major: item.major || "",
    modules: (item.modules || []).map((row) => ({
      key: row.key || "",
      name: row.name || "",
      required: Number(row.required || 0),
    })),
  });
}

function addAcademicModule() {
  academicPlanForm.modules.push({ key: "", name: "", required: 0 });
}

function removeAcademicModule(index) {
  academicPlanForm.modules.splice(index, 1);
}

async function saveAcademicPlan() {
  const modules = academicPlanForm.modules
    .map((row) => ({
      key: String(row.key || "").trim(),
      name: String(row.name || "").trim(),
      required: Number(row.required || 0),
    }))
    .filter((row) => row.key && row.name);
  const uniqueKeys = new Set(modules.map((row) => row.key));
  if (!academicPlanForm.grade.trim() || !academicPlanForm.major.trim() || !modules.length) {
    toast("请填写年级、专业和至少一个模块");
    return;
  }
  if (uniqueKeys.size !== modules.length || modules.some((row) => row.required <= 0)) {
    toast("培养方案模块键必须唯一，且要求学分必须大于 0");
    return;
  }
  const result = await withActionError(() => api.saveAcademicPlan({ grade: academicPlanForm.grade, major: academicPlanForm.major, modules }), "培养方案保存失败");
  if (!result) return;
  toast("培养方案已保存");
  await load();
}

function resetTheoryForm() {
  Object.assign(theoryForm, {
    id: "",
    stem: "",
    optionsText: "正确;错误",
    answer: "正确",
    explanation: "",
    category: "理论知识",
    online: true,
  });
}

function editTheoryQuestion(item) {
  Object.assign(theoryForm, {
    id: item.id,
    stem: item.stem,
    optionsText: (item.options || []).join(";"),
    answer: item.answer,
    explanation: item.explanation || "",
    category: item.category || "理论知识",
    online: item.online !== false,
  });
}

async function saveTheoryQuestion() {
  if (!theoryForm.stem.trim() || !theoryForm.answer.trim()) {
    toast("请填写题干和答案");
    return;
  }
  const row = {
    id: theoryForm.id || `theory_${Date.now()}`,
    stem: theoryForm.stem,
    type: "single",
    options: theoryForm.optionsText.split(/[;；]/).map((item) => item.trim()).filter(Boolean),
    answer: theoryForm.answer,
    explanation: theoryForm.explanation,
    category: theoryForm.category,
    online: theoryForm.online,
  };
  if (!row.options.length || !row.options.includes(row.answer)) {
    toast("理论题答案必须包含在选项中");
    return;
  }
  const list = theoryForm.id
    ? theoryQuestions.value.map((item) => (item.id === theoryForm.id ? row : item))
    : [row, ...theoryQuestions.value];
  const result = await withActionError(() => api.saveTheoryQuestions(list), "理论题保存失败");
  if (!result) return;
  toast("理论题库已保存");
  resetTheoryForm();
  await load();
}

function onTheoryImportFile(event) {
  theoryImportFile.value = event.target.files?.[0] || null;
  theoryImportResult.value = null;
}

async function previewTheoryImport() {
  if (!theoryImportFile.value) {
    toast("请选择题库 CSV 文件");
    return;
  }
  theoryImportResult.value = await api.importTheoryQuestions(theoryImportFile.value, { dryRun: true }).catch((error) => ({
    ok: false,
    errors: [{ row: 0, field: "file", message: error.message || "题库预检失败" }],
  }));
  toast(theoryImportResult.value.errors?.length ? "题库预检发现错误" : "题库预检通过");
}

async function commitTheoryImport() {
  if (!theoryImportFile.value) {
    toast("请选择题库 CSV 文件");
    return;
  }
  theoryImportResult.value = await api.importTheoryQuestions(theoryImportFile.value, { dryRun: false }).catch((error) => ({ ok: false, errors: [{ row: 0, field: "file", message: error.message || "题库导入失败" }] }));
  toast(theoryImportResult.value.ok ? "题库已导入" : "导入失败，请处理错误行");
  if (theoryImportResult.value.ok) await load();
}

function onAcademicPlanImportFile(event) {
  academicPlanImportFile.value = event.target.files?.[0] || null;
  academicPlanImportResult.value = null;
}

async function previewAcademicPlanImport() {
  if (!academicPlanImportFile.value) {
    toast("请选择培养方案 CSV 文件");
    return;
  }
  academicPlanImportResult.value = await api.importAcademicPlans(academicPlanImportFile.value, { dryRun: true }).catch((error) => ({ ok: false, errors: [{ row: 0, field: "file", message: error.message || "培养方案预检失败" }] }));
  toast(academicPlanImportResult.value.errors?.length ? "培养方案预检发现错误" : "培养方案预检通过");
}

async function commitAcademicPlanImport() {
  if (!academicPlanImportFile.value) {
    toast("请选择培养方案 CSV 文件");
    return;
  }
  academicPlanImportResult.value = await api.importAcademicPlans(academicPlanImportFile.value, { dryRun: false }).catch((error) => ({ ok: false, errors: [{ row: 0, field: "file", message: error.message || "培养方案导入失败" }] }));
  toast(academicPlanImportResult.value.ok ? "培养方案已导入" : "导入失败，请处理错误行");
  if (academicPlanImportResult.value.ok) await load();
}

const honorImportFile = ref(null);
const honorImportResult = ref(null);

function onHonorImportFile(event) {
  honorImportFile.value = event.target.files?.[0] || null;
  honorImportResult.value = null;
}

async function previewHonorImport() {
  if (!honorImportFile.value) {
    toast("请选择荣誉 CSV 文件");
    return;
  }
  honorImportResult.value = await api.importHonors(honorImportFile.value, { dryRun: true }).catch((error) => ({
    ok: false,
    errors: [{ row: 0, message: error.message || "荣誉预检失败" }],
  }));
  toast(honorImportResult.value.errors?.length ? "荣誉预检发现错误" : `预检通过，可导入 ${honorImportResult.value.total || 0} 条`);
}

async function commitHonorImport() {
  if (!honorImportFile.value) {
    toast("请选择荣誉 CSV 文件");
    return;
  }
  honorImportResult.value = await api.importHonors(honorImportFile.value, { dryRun: false }).catch((error) => ({
    ok: false,
    errors: [{ row: 0, message: error.message || "荣誉导入失败" }],
  }));
  toast(honorImportResult.value.ok ? `已导入 ${honorImportResult.value.total || 0} 条荣誉` : "导入失败");
  if (honorImportResult.value.ok) await load();
}

async function saveHonor() {
  if (!honorForm.title.trim() || !honorForm.winner.trim()) {
    toast("请填写荣誉名称和获奖人");
    return;
  }
  if (Number(honorForm.year) < 2000 || Number(honorForm.year) > new Date().getFullYear() + 1) {
    toast("荣誉年份不合理");
    return;
  }
  const uploaded = await withActionError(() => uploadHonorAttachments(), "荣誉附件上传失败");
  if (!uploaded) return;
  honorForm.attachments = uploaded;
  const payload = { ...honorForm, year: Number(honorForm.year) };
  if (honorForm.id) {
    const result = await withActionError(() => api.updateHonor(honorForm.id, payload), "荣誉条目更新失败");
    if (!result) return;
    toast("荣誉条目已更新");
  } else {
    const result = await withActionError(() => api.createHonor(payload), "荣誉条目创建失败");
    if (!result) return;
    toast("荣誉条目已创建");
  }
  resetHonorForm();
  await load();
}
</script>

<template>
  <div v-if="session.role === ROLES.STUDENT" class="card">
    当前为学生身份。请切换为管理老师、协同管理者或学院领导查看工作台。
  </div>

  <template v-else>
    <section class="card stack">
      <div class="row between wrap">
        <div>
          <h3>管理工作台板块</h3>
          <p class="muted">按功能域拆分管理入口，减少单页混杂操作。</p>
        </div>
        <span class="tag gray">{{ visibleWorkbenchPanels.length }} 个板块</span>
      </div>
      <div class="row wrap">
        <button
          v-for="panel in visibleWorkbenchPanels"
          :key="panel.id"
          type="button"
          :class="{ primary: activeWorkbenchPanel === panel.id }"
          :title="panel.desc"
          @click="workbenchPanel = panel.id"
        >
          {{ panel.label }}
        </button>
      </div>
      <p class="muted">{{ visibleWorkbenchPanels.find((item) => item.id === activeWorkbenchPanel)?.desc }}</p>
    </section>

    <div v-if="showWorkbenchPanel('overview')" class="stack">
      <div class="grid cols-3">
        <div class="card"><div class="muted">在册学生</div><div style="font-size:28px;font-weight:700">{{ summary?.students }}</div></div>
        <div class="card"><div class="muted">待审批</div><div style="font-size:28px;font-weight:700">{{ summary?.pendingApps }}</div></div>
        <div class="card"><div class="muted">通知批次</div><div style="font-size:28px;font-weight:700">{{ summary?.batches }}</div></div>
        <div class="card"><div class="muted">未命中词</div><div style="font-size:28px;font-weight:700">{{ misses.length || summary?.miss || 0 }}</div></div>
        <div class="card"><div class="muted">短信记录</div><div style="font-size:28px;font-weight:700">{{ sms.length || summary?.sms || 0 }}</div></div>
      </div>

      <div v-if="leader" class="section-title">领导看板</div>
      <div v-if="leader" class="card stack">
        <p>政策条目 {{ leader.knowledgeCount }} · 通知 {{ leader.noticeCount }} · 学业高风险 {{ leader.academicHighRiskStudents }} · 待审批 {{ leader.pendingApps }}</p>
        <div v-if="leader.partyProgress" class="row wrap">
          <span class="tag">入党跟踪 {{ leader.partyProgress.total }} 人</span>
          <span class="tag gray">待确认环节 {{ leader.partyProgress.pendingVerifySteps }}</span>
          <span v-for="item in leader.partyProgress.byStage || []" :key="item.key" class="tag">{{ item.name }} {{ item.count }}</span>
        </div>
        <div v-if="leader.leagueProgress" class="row wrap">
          <span class="tag">入团跟踪 {{ leader.leagueProgress.total }} 人</span>
          <span class="tag gray">待确认环节 {{ leader.leagueProgress.pendingVerifySteps }}</span>
          <span v-for="item in leader.leagueProgress.byStage || []" :key="item.key" class="tag">{{ item.name }} {{ item.count }}</span>
        </div>
      </div>
    </div>

    <div v-if="showWorkbenchPanel('approvals')" class="grid cols-2">
      <section>
        <div class="row between">
          <div class="section-title">审批处理</div>
          <button v-if="session.role === ROLES.TEACHER" type="button" @click="exportApplicationsCsv">导出 CSV</button>
        </div>
        <p v-if="session.role === ROLES.COORDINATOR" class="muted">协同管理者仅可查看申请，审批需管理老师操作。</p>
        <div class="stack">
          <article v-for="item in applications" :key="item.id" class="card">
            <div class="row between">
              <strong>{{ item.type }} · {{ item.subtype }}</strong>
              <span class="tag">{{ item.status }}</span>
            </div>
            <p>{{ item.studentId }} · {{ item.form?.reason }}</p>
            <div class="row wrap" v-if="session.role === ROLES.TEACHER">
              <button @click="openApplication(item)">详情</button>
              <button
                v-for="action in decisionButtons(item)"
                :key="action"
                :class="{ primary: action === 'approve' }"
                @click="decide(item.id, action)"
              >
                {{ decisionLabel(action) }}
              </button>
            </div>
          </article>
          <div v-if="!applications.length" class="empty card">暂无可查看申请</div>
        </div>
      </section>

      <section class="card">
        <h3>定向通知发布</h3>
        <form class="stack" @submit.prevent="publishNotice">
          <input v-model="noticeForm.title" placeholder="标题" required />
          <input v-model="noticeForm.summary" placeholder="摘要" />
          <textarea v-model="noticeForm.content" placeholder="正文"></textarea>
          <input v-model="noticeForm.tags" placeholder="标签，逗号分隔" />
          <select v-model="noticeForm.kind">
            <option value="all">全体</option>
            <option value="grade">按年级</option>
            <option value="major">按专业</option>
            <option value="class">按班级</option>
            <option value="political">按政治面貌</option>
            <option value="partyStage">按入党阶段</option>
            <option value="leagueStage">按入团阶段</option>
            <option value="extension">按扩展字段</option>
          </select>
          <input
            v-if="noticeForm.kind !== 'extension' && noticeForm.kind !== 'all'"
            v-model="noticeForm.value"
            :placeholder="noticeForm.kind === 'partyStage' ? '阶段键，如 activist / candidate' : noticeForm.kind === 'leagueStage' ? '阶段键，如 l_activist' : '规则值，如 2024级 / 软件工程 / 共青团员'"
          />
          <template v-if="noticeForm.kind === 'extension'">
            <input v-model="noticeForm.extKey" placeholder="扩展字段名，如 volunteerHours" />
            <input v-model="noticeForm.extValue" placeholder="扩展字段值，如 32" />
          </template>
          <label class="row">
            <input v-model="noticeForm.enableEmail" type="checkbox" />
            同步发送邮件（需配置 SMTP）
          </label>
          <label class="row">
            <input v-model="noticeForm.enableSmsSim" type="checkbox" />
            记录短信模拟发送
          </label>
          <label>
            定时发送
            <input v-model="noticeForm.scheduledAt" type="datetime-local" />
          </label>
          <button class="primary" :disabled="session.role === ROLES.LEADER">发布</button>
        </form>
        <h4 style="margin-top:16px">录入外部通知</h4>
        <form class="stack" @submit.prevent="importExternalNotice">
          <input v-model="noticeImportForm.title" placeholder="标题" required />
          <input v-model="noticeImportForm.summary" placeholder="摘要" />
          <textarea v-model="noticeImportForm.content" placeholder="正文"></textarea>
          <input v-model="noticeImportForm.source" placeholder="来源" />
          <button type="submit" :disabled="session.role === ROLES.LEADER">录入通知库</button>
        </form>
        <h4 style="margin-top:16px">从 URL 抓取通知</h4>
        <form class="stack" @submit.prevent="fetchNoticeFromUrl">
          <input v-model="noticeUrlForm.url" placeholder="https://..." required />
          <input v-model="noticeUrlForm.source" placeholder="来源说明" />
          <button type="submit" :disabled="session.role === ROLES.LEADER">抓取并入库</button>
        </form>
      </section>
    </div>

    <section class="card" v-if="showWorkbenchPanel('party') && session.role === ROLES.TEACHER">
      <div class="row between">
        <h3>党团校历维护（FR3 / 校历联动）</h3>
        <div class="row wrap">
          <button type="button" @click="addCalendarRow">新增节点</button>
          <button class="primary" @click="saveCalendarEvents">保存校历</button>
        </div>
      </div>
      <div v-if="!calendarEvents.length" class="empty">暂无校历节点，点击「新增节点」或等待系统从官方校历初始化。</div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>日期</th><th>标题</th><th>说明</th><th>上线</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in calendarEvents" :key="item.id">
              <td><input v-model="item.date" type="date" /></td>
              <td><input v-model="item.title" /></td>
              <td><input v-model="item.note" /></td>
              <td><input v-model="item.online" type="checkbox" /></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted">保存后学生党团页「校历要点」将同步更新；点击「刷新提醒」可为近 21 天节点生成待办。</p>
    </section>

    <section class="card" v-if="showWorkbenchPanel('party') && session.role === ROLES.TEACHER">
      <h3>党团阶段推进</h3>
      <form class="form-grid" @submit.prevent="advanceParty">
        <label>
          学生
          <select v-model="partyForm.studentId" @change="loadPartyPendingSteps">
            <option v-for="student in students" :key="student.studentId" :value="student.studentId">
              {{ student.name }} {{ student.studentId }}
            </option>
          </select>
        </label>
        <label>
          目标阶段
          <select v-model="partyForm.nextKey">
            <option v-for="stage in (partyTimeline?.stages || FLOW_STAGES)" :key="stage.key" :value="stage.key">{{ stage.name }}</option>
          </select>
        </label>
        <label class="span-2">
          备注
          <input v-model="partyForm.remark" placeholder="如：支部审批通过，进入下一阶段" />
        </label>
        <label class="span-2 row">
          <input v-model="partyForm.force" type="checkbox" />
          <span>强制推进（跳过未确认环节校验）</span>
        </label>
        <div class="span-2 row">
          <button class="primary">推进阶段</button>
        </div>
      </form>
      <div v-if="partyPendingSteps.length" class="stack" style="margin-top:16px">
        <h4>待确认环节</h4>
        <div v-for="step in partyPendingSteps" :key="step.id" class="card stack">
          <div class="row between wrap">
            <strong>{{ step.order }}. {{ step.name }}</strong>
            <button class="primary" @click="verifyPartyStep(partyForm.studentId, step.id)">确认</button>
          </div>
          <p v-if="step.materialCatalog?.length" class="muted">需准备：{{ step.materialCatalog.join("、") }}</p>
          <div v-if="step.materials?.length" class="stack compact">
            <div class="muted">已上传附件（{{ step.materials.length }}）</div>
            <div v-for="file in step.materials" :key="file.id || file.fileId || file.name" class="row between wrap">
              <span>{{ file.name || "未命名附件" }} <span class="muted" v-if="file.size">({{ file.size }} bytes)</span></span>
              <button type="button" @click="downloadStepMaterial(file)">下载附件</button>
            </div>
          </div>
          <p v-else class="muted">该环节暂无已上传附件，请谨慎确认。</p>
        </div>
      </div>
      <div v-if="partyStudentDetail?.thoughtReports?.length" class="stack" style="margin-top:16px">
        <h4>思想汇报（{{ partyStudentDetail.thoughtReports.length }}）</h4>
        <article v-for="item in partyStudentDetail.thoughtReports" :key="item.id" class="card muted">
          {{ item.quarter }} · {{ formatTime(item.submittedAt) }} · {{ item.content.slice(0, 80) }}…
        </article>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('party') && session.role === ROLES.TEACHER">
      <h3>入团阶段推进</h3>
      <form class="form-grid" @submit.prevent="advanceLeague">
        <label>
          学生
          <select v-model="leagueForm.studentId" @change="loadLeaguePendingSteps">
            <option v-for="student in students" :key="student.studentId" :value="student.studentId">
              {{ student.name }} {{ student.studentId }}
            </option>
          </select>
        </label>
        <label>
          目标阶段
          <select v-model="leagueForm.nextKey">
            <option v-for="stage in LEAGUE_STAGES" :key="stage.key" :value="stage.key">{{ stage.name }}</option>
          </select>
        </label>
        <label class="span-2">
          备注
          <input v-model="leagueForm.remark" placeholder="如：团支部审批通过" />
        </label>
        <label class="span-2 row">
          <input v-model="leagueForm.force" type="checkbox" />
          <span>强制推进（跳过未确认环节校验）</span>
        </label>
        <div class="span-2 row">
          <button class="primary">推进入团阶段</button>
          <button type="button" @click="refreshLeagueReminders">刷新入团提醒</button>
        </div>
      </form>
      <div v-if="leaguePendingSteps.length" class="stack" style="margin-top:16px">
        <h4>待确认入团环节</h4>
        <div v-for="step in leaguePendingSteps" :key="step.id" class="card stack">
          <div class="row between wrap">
            <strong>{{ step.order }}. {{ step.name }}</strong>
            <button class="primary" @click="verifyLeagueStep(leagueForm.studentId, step.id)">确认</button>
          </div>
          <p v-if="step.materialCatalog?.length" class="muted">需准备：{{ step.materialCatalog.join("、") }}</p>
          <div v-if="step.materials?.length" class="stack compact">
            <div class="muted">已上传附件（{{ step.materials.length }}）</div>
            <div v-for="file in step.materials" :key="file.id || file.fileId || file.name" class="row between wrap">
              <span>{{ file.name || "未命名附件" }} <span class="muted" v-if="file.size">({{ file.size }} bytes)</span></span>
              <button type="button" @click="downloadStepMaterial(file)">下载附件</button>
            </div>
          </div>
          <p v-else class="muted">该环节暂无已上传附件，请谨慎确认。</p>
        </div>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('party') && partyTimeline && [ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
      <div class="row between">
        <h3>党团标准时间线</h3>
        <div class="row wrap" v-if="session.role === ROLES.TEACHER">
          <button @click="refreshPartyReminders">刷新提醒</button>
          <button class="primary" @click="savePartyTimeline">保存规则</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>阶段</th><th>阶段周期(天)</th><th>提前提醒(天)</th><th>材料要求</th></tr>
          </thead>
          <tbody>
            <tr v-for="rule in partyTimeline.rules" :key="rule.stageKey">
              <td>{{ stageName(rule.stageKey) }}</td>
              <td><input v-model.number="rule.durationDays" type="number" min="0" :disabled="session.role !== ROLES.TEACHER" /></td>
              <td><input v-model.number="rule.remindBeforeDays" type="number" min="0" :disabled="session.role !== ROLES.TEACHER" /></td>
              <td><input v-model="rule.material" :disabled="session.role !== ROLES.TEACHER" /></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted">保存规则后点击刷新提醒，系统会按当前阶段为学生生成或更新待办任务。</p>
    </section>

    <section class="card" v-if="showWorkbenchPanel('party') && partyTimeline && session.role === ROLES.TEACHER">
      <div class="row between">
        <h3>党团阶段配置</h3>
        <button class="primary" @click="savePartyStages">保存阶段</button>
      </div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>键</th><th>名称</th><th>说明</th><th>排序</th></tr>
          </thead>
          <tbody>
            <tr v-for="stage in partyTimeline.stages" :key="stage.key">
              <td>{{ stage.key }}</td>
              <td><input v-model="stage.name" /></td>
              <td><input v-model="stage.desc" /></td>
              <td><input v-model.number="stage.order" type="number" min="0" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('party') && partyProgressList.length && [ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
      <div class="row between wrap">
        <h3>党团进度一览</h3>
        <div class="row wrap">
          <select v-model="partyClassFilter" @change="load">
            <option value="">全部班级</option>
            <option v-for="student in students" :key="student.className" :value="student.className">{{ student.className }}</option>
          </select>
          <button v-if="session.role === ROLES.TEACHER" @click="exportPartyProgress">导出 CSV</button>
        </div>
      </div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>学号</th><th>姓名</th><th>班级</th><th>当前阶段</th><th>环节进度</th><th>材料</th><th>思想汇报</th><th>待办</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in partyProgressList.slice(0, 30)" :key="row.studentId">
              <td>{{ row.studentId }}</td>
              <td>{{ row.name }}</td>
              <td>{{ row.className }}</td>
              <td>{{ row.currentStageName || row.currentKey }}</td>
              <td>{{ row.stepProgress || "—" }}</td>
              <td>{{ row.materialCount ?? 0 }}</td>
              <td>{{ row.thoughtReportCount ?? 0 }}</td>
              <td>{{ (row.tasks || []).filter((t) => !t.done).length }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('party') && leagueProgressList.length && [ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
      <h3>入团进度一览</h3>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>学号</th><th>姓名</th><th>班级</th><th>当前阶段</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in leagueProgressList.slice(0, 30)" :key="row.studentId">
              <td>{{ row.studentId }}</td>
              <td>{{ row.name }}</td>
              <td>{{ row.className }}</td>
              <td>{{ row.currentStageName || row.currentKey }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('party') && [ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
      <div class="row between">
        <h3>理论自测题库</h3>
        <span class="tag gray">{{ theoryQuestions.length }} 题</span>
      </div>
      <div class="grid cols-2">
        <div class="stack">
          <article v-for="item in theoryQuestions.slice(0, 8)" :key="item.id" class="card">
            <div class="row between">
              <strong>{{ item.stem }}</strong>
              <span class="tag" :class="item.online === false ? 'gray' : 'green'">{{ item.online === false ? "下线" : "上线" }}</span>
            </div>
            <p class="muted">{{ item.category }} · 答案 {{ item.answer }}</p>
            <button v-if="session.role === ROLES.TEACHER" @click="editTheoryQuestion(item)">编辑</button>
          </article>
        </div>
        <form class="form-grid" @submit.prevent="saveTheoryQuestion">
          <input v-model="theoryForm.stem" :disabled="session.role !== ROLES.TEACHER" placeholder="题干" />
          <input v-model="theoryForm.category" :disabled="session.role !== ROLES.TEACHER" placeholder="分类" />
          <input v-model="theoryForm.optionsText" :disabled="session.role !== ROLES.TEACHER" placeholder="选项，用分号分隔" />
          <input v-model="theoryForm.answer" :disabled="session.role !== ROLES.TEACHER" placeholder="答案" />
          <textarea v-model="theoryForm.explanation" class="span-2" :disabled="session.role !== ROLES.TEACHER" placeholder="解析"></textarea>
          <label class="row">
            <input v-model="theoryForm.online" type="checkbox" :disabled="session.role !== ROLES.TEACHER" />
            上线
          </label>
          <label v-if="session.role === ROLES.TEACHER">
            CSV 导入题库
            <input type="file" accept=".csv" @change="onTheoryImportFile" />
          </label>
          <div class="span-2 row wrap" v-if="session.role === ROLES.TEACHER">
            <button class="primary">{{ theoryForm.id ? "保存题目" : "新增题目" }}</button>
            <button type="button" @click="resetTheoryForm">清空</button>
            <button type="button" @click="previewTheoryImport">预检导入</button>
            <button type="button" @click="commitTheoryImport">确认导入</button>
          </div>
          <div v-if="theoryImportResult" class="span-2 card">
            <p class="muted">共 {{ theoryImportResult.total }} 行，预检题目 {{ theoryImportResult.questions?.length || 0 }} 题</p>
            <p v-for="error in theoryImportResult.errors || []" :key="`${error.row}-${error.field}`" class="muted">
              第 {{ error.row }} 行 · {{ error.field }} · {{ error.message }}
            </p>
          </div>
        </form>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('students') && session.role === ROLES.TEACHER">
      <div class="row between">
        <h3>学生画像导出</h3>
        <button class="primary" @click="exportStudents('csv')">导出 CSV</button>
        <button @click="exportStudents('xlsx')">导出 Excel</button>
        <button @click="resetStudentPassword">重置学生密码</button>
      </div>
      <p class="muted">导出默认使用脱敏手机号；导入支持 CSV，后端也预留 XLSX 解析能力。</p>
      <div class="form-grid">
        <label class="span-2">
          学生数据文件
          <input type="file" accept=".csv,.xlsx" @change="onStudentImportFile" />
        </label>
        <label class="row">
          <input v-model="studentImportOverwrite" type="checkbox" />
          覆盖已有学号
        </label>
        <div class="row wrap">
          <button @click="previewStudentImport">预检导入</button>
          <button class="primary" @click="commitStudentImport">确认导入</button>
        </div>
      </div>
      <div v-if="studentImportResult" class="stack">
        <p class="muted">
          共 {{ studentImportResult.total }} 行，预计新增 {{ studentImportResult.created }}，更新 {{ studentImportResult.updated }}
        </p>
        <div v-if="studentImportResult.errors?.length" class="card">
          <strong>错误行</strong>
          <p v-for="error in studentImportResult.errors.slice(0, 5)" :key="`${error.row}-${error.field}`" class="muted">
            第 {{ error.row }} 行 · {{ error.field }} · {{ error.message }}
          </p>
        </div>
        <div v-else class="card">
          <strong>预览</strong>
          <p v-for="row in studentImportResult.preview || []" :key="row.studentId" class="muted">
            {{ row.studentId }} · {{ row.name }} · {{ row.grade }} · {{ row.major }} · {{ row.className }}
          </p>
        </div>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('students') && [ROLES.TEACHER, ROLES.COORDINATOR].includes(session.role)">
      <div class="row between">
        <h3>学生画像维护</h3>
        <span class="tag gray">可编辑 {{ fieldPolicy?.editable?.length || 0 }} 项</span>
      </div>
      <div class="grid cols-2">
        <div class="stack">
          <article v-for="item in students.slice(0, 8)" :key="item.studentId" class="card row between">
            <span>
              {{ item.name }} · {{ item.studentId }}<br />
              <span class="muted">{{ item.className }} · {{ item.politicalStatus }}</span>
              <span v-if="item.idCardMasked" class="muted"><br />身份证 {{ item.idCardMasked }}</span>
            </span>
            <button @click="editStudent(item)">编辑</button>
          </article>
        </div>
        <form class="form-grid" @submit.prevent="saveStudentProfile">
          <input v-model="studentForm.studentId" disabled placeholder="学号" />
          <input v-model="studentForm.name" :disabled="!canEditStudentField('name')" placeholder="姓名" />
          <input v-model="studentForm.grade" :disabled="!canEditStudentField('grade')" placeholder="年级" />
          <input v-model="studentForm.major" :disabled="!canEditStudentField('major')" placeholder="专业" />
          <input v-model="studentForm.className" :disabled="!canEditStudentField('className')" placeholder="班级" />
          <input v-model="studentForm.nation" :disabled="!canEditStudentField('nation')" placeholder="民族" />
          <input v-model="studentForm.phone" :disabled="!canEditStudentField('phone')" placeholder="手机号" />
          <input v-model="studentForm.politicalStatus" :disabled="!canEditStudentField('politicalStatus')" placeholder="政治面貌" />
          <input v-model="studentForm.tutor" :disabled="!canEditStudentField('tutor')" placeholder="导师" />
          <input v-model="studentForm.hometown" :disabled="!canEditStudentField('hometown')" placeholder="生源地/户籍地" />
          <div class="span-2" v-if="canEditStudentField('idCard') || studentForm.idCardMasked">
            <label>身份证号</label>
            <p v-if="studentForm.idCardMasked" class="muted">当前脱敏：{{ studentForm.idCardMasked }}</p>
            <input
              v-model="studentForm.idCard"
              :disabled="!canEditStudentField('idCard')"
              placeholder="输入完整身份证号以更新（留空则不修改）"
            />
          </div>
          <textarea v-model="studentForm.extensionText" class="span-2" :disabled="!canEditStudentField('extension')" placeholder="扩展画像 JSON"></textarea>
          <button class="primary span-2">保存画像</button>
        </form>
      </div>
    </section>

    <section v-if="showWorkbenchPanel('academic') && [ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
      <div class="section-title">学业风险学生</div>
      <div class="stack">
        <article v-for="item in academicRisks.slice(0, 6)" :key="item.studentId" class="card">
          <div class="row between">
            <strong>{{ item.name }} · {{ item.studentId }}</strong>
            <span class="tag" :class="riskClass(item.riskLevel)">风险 {{ item.riskLevel }}</span>
          </div>
          <p class="muted">{{ item.grade }} · {{ item.major }} · {{ item.className }} · 总缺口 {{ item.totalGap }}</p>
          <p v-if="item.gaps?.length">
            <span v-for="gap in item.gaps.slice(0, 3)" :key="gap.key" class="tag gray">
              {{ gap.name }} 缺 {{ gap.gap }}
            </span>
          </p>
          <p v-else class="muted">暂无明显学分缺口或缺少学业数据。</p>
        </article>
        <div v-if="!academicRisks.length" class="empty card">暂无学业风险数据</div>
      </div>
    </section>

    <section class="card" v-if="showWorkbenchPanel('academic') && [ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
      <div class="row between">
        <h3>培养方案维护</h3>
        <span class="tag gray">{{ academicPlans.length }} 个方案</span>
      </div>
      <div class="grid cols-2">
        <div class="stack">
          <article v-for="item in academicPlans.slice(0, 6)" :key="item.key" class="card">
            <div class="row between">
              <strong>{{ item.grade }} · {{ item.major }}</strong>
              <button v-if="session.role === ROLES.TEACHER" @click="editAcademicPlan(item)">编辑</button>
            </div>
            <p class="muted">{{ item.modules?.length || 0 }} 个模块 · 总要求 {{ (item.modules || []).reduce((sum, row) => sum + Number(row.required || 0), 0) }} 学分</p>
          </article>
        </div>
        <form class="form-grid" @submit.prevent="saveAcademicPlan">
          <input v-model="academicPlanForm.grade" :disabled="session.role !== ROLES.TEACHER" placeholder="年级，如 2024级" />
          <input v-model="academicPlanForm.major" :disabled="session.role !== ROLES.TEACHER" placeholder="专业，如 软件工程" />
          <div class="span-2 table-wrap" v-if="session.role === ROLES.TEACHER || academicPlanForm.modules.length">
            <table class="table">
              <thead>
                <tr><th>模块 key</th><th>模块名称</th><th>要求学分</th><th v-if="session.role === ROLES.TEACHER">操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in academicPlanForm.modules" :key="`${row.key}-${index}`">
                  <td><input v-model="row.key" :disabled="session.role !== ROLES.TEACHER" placeholder="major_core" /></td>
                  <td><input v-model="row.name" :disabled="session.role !== ROLES.TEACHER" placeholder="专业核心" /></td>
                  <td><input v-model.number="row.required" type="number" min="0" :disabled="session.role !== ROLES.TEACHER" /></td>
                  <td v-if="session.role === ROLES.TEACHER"><button type="button" @click="removeAcademicModule(index)">删除</button></td>
                </tr>
              </tbody>
            </table>
            <button v-if="session.role === ROLES.TEACHER" type="button" @click="addAcademicModule">添加模块</button>
          </div>
          <label class="span-2" v-if="session.role === ROLES.TEACHER">
            CSV 导入培养方案
            <input type="file" accept=".csv" @change="onAcademicPlanImportFile" />
          </label>
          <div class="span-2 row wrap" v-if="session.role === ROLES.TEACHER">
            <button class="primary">保存方案</button>
            <button type="button" @click="previewAcademicPlanImport">预检导入</button>
            <button type="button" @click="commitAcademicPlanImport">确认导入</button>
          </div>
          <div v-if="academicPlanImportResult" class="span-2 card">
            <p class="muted">共 {{ academicPlanImportResult.total }} 行，涉及 {{ academicPlanImportResult.plans?.length || 0 }} 个方案</p>
            <p v-for="error in academicPlanImportResult.errors || []" :key="`${error.row}-${error.field}`" class="muted">
              第 {{ error.row }} 行 · {{ error.field }} · {{ error.message }}
            </p>
          </div>
        </form>
      </div>
    </section>

    <div v-if="showWorkbenchPanel('honors')" class="grid cols-2">
      <section class="card" v-if="session.role === ROLES.TEACHER">
        <h3>荣誉展示维护</h3>
        <form class="form-grid" @submit.prevent="saveHonor">
          <input v-model="honorForm.title" placeholder="荣誉名称" />
          <input v-model="honorForm.winner" placeholder="获奖人" />
          <input v-model="honorForm.year" type="number" placeholder="年份" />
          <input v-model="honorForm.category" placeholder="类别" />
          <input v-model="honorForm.grade" placeholder="年级" />
          <input v-model="honorForm.major" placeholder="专业" />
          <textarea v-model="honorForm.intro" class="span-2" placeholder="简介"></textarea>
          <select v-model="honorForm.visibility">
            <option value="public">附件公开</option>
            <option value="restricted">附件限管理端</option>
          </select>
          <label>
            证明材料
            <input type="file" multiple @change="onHonorFiles" />
          </label>
          <p v-if="honorForm.attachments.length" class="muted span-2">
            已绑定 {{ honorForm.attachments.length }} 个材料：
            <span v-for="file in honorForm.attachments" :key="file.id || file.name" class="tag gray">{{ file.name }}</span>
          </p>
          <div class="span-2 row">
            <button class="primary">{{ honorForm.id ? "保存荣誉" : "新增荣誉" }}</button>
            <button type="button" @click="resetHonorForm">清空</button>
          </div>
        </form>
        <h4 style="margin-top:20px">CSV 批量导入</h4>
        <p class="muted">列名：标题、获奖人、年份（必填）；可选：类别、年级、专业、简介</p>
        <div class="row wrap">
          <input type="file" accept=".csv,text/csv" @change="onHonorImportFile" />
          <button type="button" @click="previewHonorImport">预检</button>
          <button type="button" class="primary" @click="commitHonorImport">确认导入</button>
        </div>
        <div v-if="honorImportResult?.errors?.length" class="stack compact" style="margin-top:12px">
          <p v-for="err in honorImportResult.errors" :key="`${err.row}-${err.message}`" class="muted">第 {{ err.row }} 行：{{ err.message }}</p>
        </div>
      </section>

      <section>
        <div class="section-title">荣誉条目</div>
        <div class="stack">
          <article v-for="item in honors.slice(0, 5)" :key="item.id" class="card">
            <strong>{{ item.title }}</strong>
            <span class="tag" :class="item.online === false ? 'gray' : 'green'">{{ item.online === false ? "已下线" : "展示中" }}</span>
            <p class="muted">{{ item.winner }} · {{ item.year }} · {{ item.category }}</p>
            <p>{{ item.intro }}</p>
            <p v-if="item.attachments?.length" class="muted">证明材料 {{ item.attachments.length }} 个 · {{ item.visibility === "restricted" ? "限管理端" : "公开" }}</p>
            <div class="row wrap" v-if="session.role === ROLES.TEACHER">
              <button @click="editHonor(item)">编辑</button>
              <button @click="toggleHonorOnline(item)">{{ item.online === false ? "上线" : "下线" }}</button>
              <button @click="deleteHonor(item.id)">删除</button>
            </div>
          </article>
          <div v-if="!honors.length" class="empty card">暂无荣誉条目</div>
        </div>
      </section>
    </div>

    <section v-if="showWorkbenchPanel('approvals') && selectedApplication" class="card">
      <div class="row between">
        <h3>审批详情</h3>
        <span class="tag">{{ selectedApplication.status }}</span>
      </div>
      <p>{{ selectedApplication.studentId }} · {{ selectedApplication.type }} · {{ selectedApplication.subtype }}</p>
      <p class="muted">说明：{{ selectedApplication.form?.reason || "未填写" }}</p>
      <div class="section-title">审批轨迹</div>
      <div class="stack">
        <div v-for="row in selectedApplication.auditTrail || []" :key="`${row.at}-${row.action}`" class="card muted">
          {{ formatTime(row.at) }} · {{ row.actor }} · {{ row.action }}
          <span v-if="row.remark"> · {{ row.remark }}</span>
        </div>
      </div>
    </section>

    <WorkbenchBatchTable
      v-if="showWorkbenchPanel('approvals')"
      :batches="batches"
      :batch-filter="batchFilter"
      :can-dispatch="session.role === ROLES.TEACHER"
      @apply-filter="applyBatchFilter"
      @dispatch-scheduled="dispatchScheduled"
    />

    <div v-if="showWorkbenchPanel('knowledge')" class="section-title">高频未命中词</div>
    <div v-if="showWorkbenchPanel('knowledge')" class="stack">
      <div v-for="item in misses.slice(0, 20)" :key="item.keyword" class="card row between">
        <strong>{{ item.keyword }}</strong>
        <span class="tag">{{ item.count }} 次</span>
        <span v-if="item.lastAt" class="muted">{{ formatTime(item.lastAt) }}</span>
        <button v-if="session.role === ROLES.TEACHER" @click="fillFromMiss(item)">转为知识</button>
      </div>
      <div v-if="!misses.length" class="empty card">暂无未命中词记录</div>
    </div>

    <div v-if="showWorkbenchPanel('knowledge')" class="grid cols-2">
      <section class="card">
        <h3>知识库维护</h3>
        <div class="row wrap" v-if="session.role === ROLES.TEACHER" style="margin-bottom:12px">
          <button type="button" @click="exportKnowledgeCsv">导出知识库 CSV</button>
        </div>
        <form class="stack" @submit.prevent="saveKnowledge">
          <input v-model="knowledgeForm.title" placeholder="标题" :disabled="session.role !== ROLES.TEACHER" />
          <input v-model="knowledgeForm.category" placeholder="分类" :disabled="session.role !== ROLES.TEACHER" />
          <input v-model="knowledgeForm.tags" placeholder="标签，逗号分隔" :disabled="session.role !== ROLES.TEACHER" />
          <textarea v-model="knowledgeForm.summary" placeholder="标准摘要" :disabled="session.role !== ROLES.TEACHER"></textarea>
          <textarea v-model="knowledgeForm.body" placeholder="详细依据、办理步骤" :disabled="session.role !== ROLES.TEACHER && session.role !== ROLES.COORDINATOR"></textarea>
          <input v-model="knowledgeForm.officialLink" placeholder="官方链接（可选）" :disabled="session.role !== ROLES.TEACHER && session.role !== ROLES.COORDINATOR" />
          <label>
            政策附件
            <input type="file" multiple :disabled="session.role !== ROLES.TEACHER" @change="onKnowledgeFiles" />
          </label>
          <p v-if="knowledgeForm.attachments.length" class="muted">
            已绑定 {{ knowledgeForm.attachments.length }} 个附件：
            <span v-for="file in knowledgeForm.attachments" :key="file.id || file.name" class="tag gray">{{ file.name }}</span>
          </p>
          <label class="row">
            <input v-model="knowledgeForm.sensitiveHint" type="checkbox" :disabled="session.role !== ROLES.TEACHER" />
            敏感内容仅展示摘要
          </label>
          <label class="row">
            <input v-model="knowledgeForm.online" type="checkbox" :disabled="session.role !== ROLES.TEACHER && session.role !== ROLES.COORDINATOR" />
            上线展示
          </label>
          <div class="row wrap" v-if="session.role === ROLES.TEACHER || session.role === ROLES.COORDINATOR">
            <button class="primary">{{ knowledgeForm.id ? "保存修改" : "创建条目" }}</button>
            <button type="button" @click="resetKnowledgeForm">清空</button>
          </div>
        </form>
      </section>

      <section>
        <div class="section-title">知识条目</div>
        <div class="stack">
          <article v-for="item in knowledgeItems.slice(0, 6)" :key="item.id" class="card">
            <div class="row between">
              <strong>{{ item.title }}</strong>
              <span class="tag" :class="item.online === false ? 'gray' : 'green'">{{ item.online === false ? "下线" : "上线" }}</span>
            </div>
            <p class="muted">{{ item.category }} · 命中 {{ item.hitCount || 0 }}</p>
            <p>{{ item.summary }}</p>
            <p v-if="item.attachments?.length" class="muted">附件 {{ item.attachments.length }} 个</p>
            <div class="row wrap" v-if="session.role === ROLES.TEACHER">
              <button @click="editKnowledge(item)">编辑</button>
              <button @click="toggleKnowledge(item)">{{ item.online === false ? "上线" : "下线" }}</button>
            </div>
          </article>
          <div v-if="!knowledgeItems.length" class="empty card">暂无知识条目</div>
        </div>
      </section>
    </div>

    <div class="grid cols-2" v-if="showWorkbenchPanel('knowledge') && [ROLES.TEACHER, ROLES.COORDINATOR].includes(session.role)">
      <section class="card">
        <h3>常用模板维护</h3>
        <form class="stack" @submit.prevent="saveWorkbenchTemplate">
          <input v-model="templateForm.name" placeholder="模板名称" required />
          <input v-model="templateForm.scene" placeholder="适用场景" />
          <input v-model="templateForm.format" placeholder="格式 docx/xlsx" />
          <input type="file" @change="(e) => (templateFile = e.target.files?.[0] || null)" />
          <button class="primary">{{ templateForm.id ? "保存模板" : "新建模板" }}</button>
        </form>
        <div class="stack" style="margin-top:12px">
          <div v-for="item in workbenchTemplates" :key="item.id" class="card row between">
            <span>{{ item.name }} · {{ item.scene }}</span>
            <div class="row">
              <button @click="editWorkbenchTemplate(item)">编辑</button>
              <button v-if="session.role === ROLES.TEACHER" @click="deleteWorkbenchTemplate(item.id)">删除</button>
            </div>
          </div>
        </div>
      </section>
      <section class="card">
        <h3>证明/申请 HTML 模板</h3>
        <form class="stack" @submit.prevent="saveAppTemplate">
          <input v-model="appTemplateForm.name" placeholder="模板名称" required />
          <input v-model="appTemplateForm.applyType" placeholder="申请类型" />
          <input v-model="appTemplateForm.subtype" placeholder="子类（可选）" />
          <textarea v-model="appTemplateForm.bodyHtml" placeholder="HTML，可用 {{name}} {{studentId}} {{reason}} 等占位符" rows="6"></textarea>
          <button class="primary">{{ appTemplateForm.id ? "保存" : "创建" }}</button>
        </form>
        <div class="stack" style="margin-top:12px">
          <div v-for="item in appTemplates" :key="item.id" class="card row between">
            <span>{{ item.name }} · {{ item.applyType }}</span>
            <div class="row">
              <button @click="editAppTemplate(item)">编辑</button>
              <button @click="deleteAppTemplate(item.id)">删除</button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-if="showWorkbenchPanel('audit')" class="row between">
      <div class="section-title">审计日志</div>
      <button v-if="session.role === ROLES.TEACHER" type="button" @click="exportAuditLogsCsv">导出 CSV</button>
    </div>
    <div v-if="showWorkbenchPanel('audit')" class="stack">
      <div v-for="item in logs" :key="item.id" class="card muted">
        {{ formatTime(item.at) }} · {{ item.role }} · {{ item.actorId }} · {{ item.action }} → {{ item.target }}
      </div>
    </div>
  </template>
</template>
