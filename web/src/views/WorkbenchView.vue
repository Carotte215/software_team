<script setup>
import { inject, onMounted, reactive, ref } from "vue";
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
const partyTimeline = ref(null);
const fieldPolicy = ref(null);
const studentImportFile = ref(null);
const studentImportOverwrite = ref(false);
const studentImportResult = ref(null);
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
  extensionText: "{}",
});
const noticeForm = reactive({
  title: "",
  summary: "",
  content: "",
  tags: "通知,党团",
  kind: "all",
  value: "",
  scheduledAt: "",
});
const batchFilter = reactive({
  title: "",
  batchId: "",
  status: "",
});
const knowledgeForm = reactive({
  id: "",
  title: "",
  category: "常见问题",
  tags: "",
  summary: "",
  body: "",
  sensitiveHint: false,
  online: true,
  attachments: [],
});
const partyForm = reactive({
  studentId: "",
  nextKey: "activist",
  remark: "",
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

onMounted(load);

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
  honors.value = (await api.listHonors().catch(() => ({ list: [] }))).list || [];
  academicRisks.value = (await api.listAcademicRisks().catch(() => ({ list: [] }))).list || [];
  partyTimeline.value = await api.getPartyTimeline().catch(() => null);
  if (!partyForm.studentId && students.value.length) partyForm.studentId = students.value[0].studentId;
  logs.value = (await api.listAuditLogs({ limit: 20 }).catch(() => ({ list: [] }))).list || [];
  leader.value = session.value.role === ROLES.LEADER
    ? await api.getLeaderDashboard().catch(() => null)
    : null;
}

async function publishNotice() {
  const tags = noticeForm.tags.split(/[,，]/).map((item) => item.trim()).filter(Boolean);
  const result = await api.publishNotice({
    title: noticeForm.title,
    summary: noticeForm.summary,
    content: noticeForm.content,
    tags,
    targetRule: { kind: noticeForm.kind, value: noticeForm.value },
    scheduledAt: noticeForm.scheduledAt ? new Date(noticeForm.scheduledAt).getTime() : 0,
  });
  toast(result.scheduled ? "已生成定时通知批次" : "已生成通知批次");
  Object.assign(noticeForm, { title: "", summary: "", content: "", tags: "通知,党团", kind: "all", value: "", scheduledAt: "" });
  await load();
}

function batchQuery() {
  return {
    title: batchFilter.title,
    batchId: batchFilter.batchId,
    status: batchFilter.status,
  };
}

async function applyBatchFilter() {
  batches.value = (await api.listWorkbenchBatches(batchQuery()).catch(() => ({ list: [] }))).list || [];
}

async function dispatchScheduled() {
  const result = await api.dispatchScheduledNotices();
  toast(`已派发 ${result.dispatched} 个到期批次`);
  await load();
}

async function decide(id, action) {
  const message = action === "reject" ? "驳回原因" : "审批意见";
  const text = window.prompt(message, action === "reject" ? "材料不全，请补充后重提。" : "同意。") || "";
  const payload = action === "reject" ? { reason: text } : { comment: text };
  await api.decideApplication(id, action, payload);
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
  knowledgeForm.attachments = await uploadKnowledgeAttachments();
  if (knowledgeForm.id) {
    await api.updateKnowledge(knowledgeForm.id, knowledgePayload());
    toast("知识条目已更新");
  } else {
    await api.createKnowledge(knowledgePayload());
    toast("知识条目已创建");
  }
  resetKnowledgeForm();
  await load();
}

async function toggleKnowledge(item) {
  await api.setKnowledgeOnline(item.id, item.online === false);
  toast(item.online === false ? "已上线" : "已下线");
  await load();
}

async function advanceParty() {
  if (!partyForm.studentId || !partyForm.nextKey) {
    toast("请选择学生和目标阶段");
    return;
  }
  await api.advancePartyStage({ ...partyForm });
  toast("党团阶段已推进");
  partyForm.remark = "";
  await load();
}

function stageName(key) {
  return FLOW_STAGES.find((stage) => stage.key === key)?.name || key;
}

async function savePartyTimeline() {
  if (!partyTimeline.value?.rules?.length) {
    toast("暂无可保存的时间线规则");
    return;
  }
  partyTimeline.value = await api.updatePartyTimeline(partyTimeline.value.rules);
  toast("党团标准时间线已保存");
}

async function refreshPartyReminders() {
  const result = await api.refreshPartyReminders();
  toast(`已刷新 ${result.changed} 名学生的提醒任务`);
  await load();
}

async function exportStudents() {
  const blob = await api.exportStudents();
  saveBlob(blob, "学生画像导出.csv");
  toast("学生画像导出已开始");
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
  await api.updateStudent(studentForm.studentId, payload);
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
  });
  toast(studentImportResult.value.errors?.length ? "导入预检发现错误" : "导入预检通过");
}

async function commitStudentImport() {
  if (!studentImportFile.value) {
    toast("请选择 CSV 或 XLSX 文件");
    return;
  }
  studentImportResult.value = await api.importStudents(studentImportFile.value, {
    dryRun: false,
    overwrite: studentImportOverwrite.value,
  });
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

async function saveHonor() {
  if (!honorForm.title.trim() || !honorForm.winner.trim()) {
    toast("请填写荣誉名称和获奖人");
    return;
  }
  honorForm.attachments = await uploadHonorAttachments();
  const payload = { ...honorForm, year: Number(honorForm.year) };
  if (honorForm.id) {
    await api.updateHonor(honorForm.id, payload);
    toast("荣誉条目已更新");
  } else {
    await api.createHonor(payload);
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
    <div class="grid cols-3">
      <div class="card"><div class="muted">在册学生</div><div style="font-size:28px;font-weight:700">{{ summary?.students }}</div></div>
      <div class="card"><div class="muted">待审批</div><div style="font-size:28px;font-weight:700">{{ summary?.pendingApps }}</div></div>
      <div class="card"><div class="muted">通知批次</div><div style="font-size:28px;font-weight:700">{{ summary?.batches }}</div></div>
      <div class="card"><div class="muted">未命中词</div><div style="font-size:28px;font-weight:700">{{ misses.length || summary?.miss || 0 }}</div></div>
      <div class="card"><div class="muted">短信模拟</div><div style="font-size:28px;font-weight:700">{{ sms.length || summary?.sms || 0 }}</div></div>
    </div>

    <div v-if="leader" class="section-title">领导看板</div>
    <div v-if="leader" class="card">
      政策条目 {{ leader.knowledgeCount }} · 通知 {{ leader.noticeCount }} · 学业高风险 {{ leader.academicHighRiskStudents }}
    </div>

    <div class="grid cols-2">
      <section>
        <div class="section-title">审批处理</div>
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
          </select>
          <input v-model="noticeForm.value" placeholder="规则值，如 2024级 / 软件工程" />
          <label>
            定时发送
            <input v-model="noticeForm.scheduledAt" type="datetime-local" />
          </label>
          <button class="primary" :disabled="session.role === ROLES.LEADER">发布</button>
        </form>
      </section>
    </div>

    <section class="card" v-if="session.role === ROLES.TEACHER">
      <h3>党团阶段推进</h3>
      <form class="form-grid" @submit.prevent="advanceParty">
        <label>
          学生
          <select v-model="partyForm.studentId">
            <option v-for="student in students" :key="student.studentId" :value="student.studentId">
              {{ student.name }} {{ student.studentId }}
            </option>
          </select>
        </label>
        <label>
          目标阶段
          <select v-model="partyForm.nextKey">
            <option v-for="stage in FLOW_STAGES" :key="stage.key" :value="stage.key">{{ stage.name }}</option>
          </select>
        </label>
        <label class="span-2">
          备注
          <input v-model="partyForm.remark" placeholder="如：支部审批通过，进入下一阶段" />
        </label>
        <div class="span-2 row">
          <button class="primary">推进阶段</button>
        </div>
      </form>
    </section>

    <section class="card" v-if="partyTimeline && [ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
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

    <section class="card" v-if="session.role === ROLES.TEACHER">
      <div class="row between">
        <h3>学生画像导出</h3>
        <button class="primary" @click="exportStudents">导出 CSV</button>
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

    <section class="card" v-if="[ROLES.TEACHER, ROLES.COORDINATOR].includes(session.role)">
      <div class="row between">
        <h3>学生画像维护</h3>
        <span class="tag gray">可编辑 {{ fieldPolicy?.editable?.length || 0 }} 项</span>
      </div>
      <div class="grid cols-2">
        <div class="stack">
          <article v-for="item in students.slice(0, 8)" :key="item.studentId" class="card row between">
            <span>{{ item.name }} · {{ item.studentId }}<br /><span class="muted">{{ item.className }} · {{ item.politicalStatus }}</span></span>
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
          <textarea v-model="studentForm.extensionText" class="span-2" :disabled="!canEditStudentField('extension')" placeholder="扩展画像 JSON"></textarea>
          <button class="primary span-2">保存画像</button>
        </form>
      </div>
    </section>

    <section v-if="[ROLES.TEACHER, ROLES.LEADER].includes(session.role)">
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

    <div class="grid cols-2">
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
      </section>

      <section>
        <div class="section-title">荣誉条目</div>
        <div class="stack">
          <article v-for="item in honors.slice(0, 5)" :key="item.id" class="card">
            <strong>{{ item.title }}</strong>
            <p class="muted">{{ item.winner }} · {{ item.year }} · {{ item.category }}</p>
            <p>{{ item.intro }}</p>
            <p v-if="item.attachments?.length" class="muted">证明材料 {{ item.attachments.length }} 个 · {{ item.visibility === "restricted" ? "限管理端" : "公开" }}</p>
            <button v-if="session.role === ROLES.TEACHER" @click="editHonor(item)">编辑</button>
          </article>
          <div v-if="!honors.length" class="empty card">暂无荣誉条目</div>
        </div>
      </section>
    </div>

    <section v-if="selectedApplication" class="card">
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

    <div class="row between">
      <div class="section-title">批次统计</div>
      <div class="row wrap">
        <input v-model="batchFilter.title" placeholder="标题筛选" />
        <input v-model="batchFilter.batchId" placeholder="批次号" />
        <select v-model="batchFilter.status">
          <option value="">全部状态</option>
          <option value="sent">已发送</option>
          <option value="scheduled">待发送</option>
        </select>
        <button @click="applyBatchFilter">筛选</button>
        <button v-if="session.role === ROLES.TEACHER" class="primary" @click="dispatchScheduled">派发到期</button>
      </div>
    </div>
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr><th>批次</th><th>状态</th><th>渠道</th><th>发送/失败</th><th>送达/失败</th><th>已读</th><th>可观测性</th></tr>
        </thead>
        <tbody>
          <template v-for="batch in batches" :key="batch.id">
            <tr v-for="channel in batch.channels" :key="`${batch.id}-${channel.name}`">
              <td>
                {{ batch.title }}<br />
                <span class="muted">{{ batch.id }}</span>
                <span v-if="batch.scheduledAt" class="muted"><br />{{ formatTime(batch.scheduledAt) }}</span>
              </td>
              <td><span class="tag" :class="batch.status === 'scheduled' ? 'orange' : 'green'">{{ batch.status === "scheduled" ? "待发送" : "已发送" }}</span></td>
              <td>{{ channel.name }}</td>
              <td>{{ channel.sendOk }}/{{ channel.sendFail }}</td>
              <td>{{ channel.deliverOk }}/{{ channel.deliverFail }}</td>
              <td>{{ channel.read }}</td>
              <td>{{ channel.observability || "可观测" }}</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <div class="section-title">高频未命中词</div>
    <div class="stack">
      <div v-for="item in misses.slice(0, 5)" :key="item.keyword" class="card row between">
        <strong>{{ item.keyword }}</strong>
        <span class="tag">{{ item.count }} 次</span>
        <button v-if="session.role === ROLES.TEACHER" @click="fillFromMiss(item)">转为知识</button>
      </div>
      <div v-if="!misses.length" class="empty card">暂无未命中词记录</div>
    </div>

    <div class="grid cols-2">
      <section class="card">
        <h3>知识库维护</h3>
        <form class="stack" @submit.prevent="saveKnowledge">
          <input v-model="knowledgeForm.title" placeholder="标题" :disabled="session.role !== ROLES.TEACHER" />
          <input v-model="knowledgeForm.category" placeholder="分类" :disabled="session.role !== ROLES.TEACHER" />
          <input v-model="knowledgeForm.tags" placeholder="标签，逗号分隔" :disabled="session.role !== ROLES.TEACHER" />
          <textarea v-model="knowledgeForm.summary" placeholder="标准摘要" :disabled="session.role !== ROLES.TEACHER"></textarea>
          <textarea v-model="knowledgeForm.body" placeholder="详细依据、办理步骤或官方链接" :disabled="session.role !== ROLES.TEACHER"></textarea>
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
            <input v-model="knowledgeForm.online" type="checkbox" :disabled="session.role !== ROLES.TEACHER" />
            上线展示
          </label>
          <div class="row wrap" v-if="session.role === ROLES.TEACHER">
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

    <div class="section-title">审计日志</div>
    <div class="stack">
      <div v-for="item in logs" :key="item.id" class="card muted">
        {{ formatTime(item.at) }} · {{ item.role }} · {{ item.actorId }} · {{ item.action }} → {{ item.target }}
      </div>
    </div>
  </template>
</template>
