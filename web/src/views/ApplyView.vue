<script setup>
import { computed, inject, onMounted, reactive, ref } from "vue";
import { APPROVAL } from "../data/seed.js";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const applications = ref([]);
const selected = ref(null);
const form = reactive({
  id: "",
  status: "",
  type: "证明申请",
  subtype: "在读证明",
  reason: "",
  startDate: "",
  endDate: "",
  idCard: "",
  partyJoinDate: "",
  partyBranch: "",
  leagueJoinDate: "",
  memberNo: "",
  offlineHandoff: false,
  files: [],
});

const LEAVE_SUBTYPES = ["事假", "病假", "其他"];
const SEAL_SUBTYPES = ["行政用印", "社团用印", "其他"];

const showCertFields = computed(() => form.type === "证明申请" && ["党员证明", "团员证明"].includes(form.subtype));
const showLeaveDates = computed(() => form.type === "请假申请");
const isSeal = computed(() => form.type === "盖章申请");
const officialGuide = ref(null);
const certHints = computed(() => {
  if (form.subtype === "党员证明") return officialGuide.value?.certFields?.party || [];
  if (form.subtype === "团员证明") return officialGuide.value?.certFields?.league || [];
  return [];
});

onMounted(load);

async function load() {
  const [res, draft, guide] = await Promise.all([
    api.listApplications(),
    api.getApplicationDraft().catch(() => null),
    api.getPartyOfficialGuide().catch(() => null),
  ]);
  applications.value = res.list || [];
  officialGuide.value = guide;
  if (draft && !form.id) fillForm(draft);
}

function onFiles(event) {
  form.files = Array.from(event.target.files || []);
}

function isNativeFile(item) {
  return typeof File !== "undefined" && item instanceof File;
}

function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

async function uploadAttachments() {
  return Promise.all(form.files.map(async (item) => (isNativeFile(item) ? api.uploadFile(item, form.type) : item)));
}

async function buildPayload() {
  const attachments = await uploadAttachments();
  return {
    type: form.type,
    subtype: form.subtype,
    form: {
      reason: form.reason,
      startDate: form.startDate,
      endDate: form.endDate,
      idCard: form.idCard,
      partyJoinDate: form.partyJoinDate,
      partyBranch: form.partyBranch,
      leagueJoinDate: form.leagueJoinDate,
      memberNo: form.memberNo,
      offlineHandoff: form.offlineHandoff,
    },
    attachments,
  };
}

function validateForm() {
  if (form.type === "证明申请") {
    const certErr = validateCertForm();
    if (certErr) return certErr;
    if (!form.reason.trim()) return "请填写申请说明";
    return "";
  }
  if (form.type === "请假申请") {
    if (!form.reason.trim()) return "请假须填写事由";
    if (!form.startDate || !form.endDate) return "请假须填写起止日期";
    if (form.startDate > form.endDate) return "开始日期不能晚于结束日期";
    return "";
  }
  if (form.type === "盖章申请") {
    if (!form.reason.trim()) return "请填写用印说明";
    if (!form.files.length) return "盖章申请须上传附件";
    if (form.offlineHandoff && !form.reason.includes("线下")) {
      return "涉密转线下请在说明中备注线下流转方式";
    }
    return "";
  }
  return "";
}

function validateCertForm() {
  if (form.type !== "证明申请") return "";
  if (form.subtype === "党员证明") {
    if (!form.idCard.trim()) return "党员证明须填写身份证号";
    if (!form.partyJoinDate) return "党员证明须填写入党时间";
    if (!form.partyBranch.trim()) return "党员证明须填写所在党支部";
  }
  if (form.subtype === "团员证明") {
    if (!form.idCard.trim()) return "团员证明须填写身份证号";
    if (!form.leagueJoinDate) return "团员证明须填写入团时间";
    if (!form.memberNo.trim()) return "团员证明须填写团员编号";
  }
  return "";
}

function fillForm(item) {
  Object.assign(form, {
    id: item.id || "",
    status: item.status || "",
    type: item.type || "证明申请",
    subtype: item.subtype || "在读证明",
    reason: item.form?.reason || "",
    startDate: item.form?.startDate || "",
    endDate: item.form?.endDate || "",
    idCard: item.form?.idCard || "",
    partyJoinDate: item.form?.partyJoinDate || "",
    partyBranch: item.form?.partyBranch || "",
    leagueJoinDate: item.form?.leagueJoinDate || "",
    memberNo: item.form?.memberNo || "",
    offlineHandoff: Boolean(item.form?.offlineHandoff),
    files: item.attachments || [],
  });
  selected.value = item;
}

function resetForm() {
  Object.assign(form, {
    id: "",
    status: "",
    type: "证明申请",
    subtype: "在读证明",
    reason: "",
    startDate: "",
    endDate: "",
    idCard: "",
    partyJoinDate: "",
    partyBranch: "",
    leagueJoinDate: "",
    memberNo: "",
    offlineHandoff: false,
    files: [],
  });
}

function onTypeChange() {
  if (form.type === "证明申请") form.subtype = "在读证明";
  else if (form.type === "请假申请") form.subtype = "事假";
  else if (form.type === "盖章申请") form.subtype = "行政用印";
}

async function saveDraft() {
  const draft = await api.saveApplicationDraft(await buildPayload());
  fillForm(draft);
  toast("草稿已保存");
  await load();
}

const previewHtml = ref("");

async function previewDocument() {
  const err = validateForm();
  if (err) {
    toast(err);
    return;
  }
  if (form.type === "盖章申请") {
    toast("盖章申请无需文档预览，请直接提交");
    return;
  }
  const payload = await buildPayload();
  const res = await api.previewApplication(payload);
  previewHtml.value = res.html || "";
  toast("已生成预览");
}

async function submit() {
  const err = validateForm();
  if (err) {
    toast(err);
    return;
  }
  const payload = await buildPayload();
  if (form.id && [APPROVAL.DRAFT, APPROVAL.REJECTED].includes(form.status)) {
    await api.submitApplicationById(form.id, payload);
    toast(form.status === APPROVAL.REJECTED ? "已重新提交审批" : "草稿已提交审批");
  } else {
    await api.submitApplication(payload);
    toast("已提交审批");
  }
  resetForm();
  await load();
}

async function openDetail(item) {
  selected.value = await api.getApplication(item.id).catch(() => item);
}

async function downloadAttachment(file) {
  if (!file?.id && !file?.url) {
    toast("该附件暂无可下载文件，请联系管理员确认材料状态");
    return;
  }
  try {
    const blob = await api.downloadFile(file);
    saveBlob(blob, file.name || "attachment");
  } catch (error) {
    toast(error.message || "附件下载失败");
  }
}

async function downloadDocument(item, format = "pdf") {
  try {
    const blob = await api.downloadApplicationDocument(item.id, format);
    saveBlob(blob, `${item.type}-${item.subtype || item.id}.${format === "pdf" ? "pdf" : "doc"}`);
    toast("文档已生成");
  } catch (error) {
    toast(error.message || "文档生成失败");
  }
}
</script>

<template>
  <div class="grid cols-2">
    <section class="card">
      <h3>发起办事申请</h3>
      <form class="form-grid" @submit.prevent="submit">
        <div v-if="form.id" class="span-2 muted">
          正在编辑：{{ form.id }} · {{ form.status }}
        </div>
        <label>
          申请类型
          <select v-model="form.type" @change="onTypeChange">
            <option>证明申请</option>
            <option>请假申请</option>
            <option>盖章申请</option>
          </select>
        </label>
        <label>
          子类
          <select v-if="form.type === '证明申请'" v-model="form.subtype">
            <option>在读证明</option>
            <option>党员证明</option>
            <option>团员证明</option>
          </select>
          <select v-else-if="form.type === '请假申请'" v-model="form.subtype">
            <option v-for="item in LEAVE_SUBTYPES" :key="item">{{ item }}</option>
          </select>
          <select v-else v-model="form.subtype">
            <option v-for="item in SEAL_SUBTYPES" :key="item">{{ item }}</option>
          </select>
        </label>
        <label class="span-2">
          申请说明
          <textarea v-model="form.reason" placeholder="请填写事由；涉密内容请备注并转线下流程"></textarea>
        </label>
        <template v-if="showCertFields">
          <div class="span-2 card muted cert-hints">
            <strong>官方证明模板填写要点</strong>
            <p v-for="field in certHints" :key="field.key">{{ field.label }}：{{ field.hint }}</p>
            <p v-if="officialGuide?.meta">开具单位：{{ form.subtype === "党员证明" ? officialGuide.meta.partyOrg : officialGuide.meta.leagueOrg }} · 咨询 {{ officialGuide.meta.contactPhone }}</p>
          </div>
          <label>
            身份证号
            <input v-model="form.idCard" placeholder="用于证明正文填写" />
          </label>
          <label v-if="form.subtype === '党员证明'">
            入党时间
            <input v-model="form.partyJoinDate" type="date" />
          </label>
          <label v-if="form.subtype === '党员证明'">
            所在党支部
            <input v-model="form.partyBranch" placeholder="如：学生第一党支部" />
          </label>
          <label v-if="form.subtype === '团员证明'">
            入团时间
            <input v-model="form.leagueJoinDate" type="date" />
          </label>
          <label v-if="form.subtype === '团员证明'">
            团员编号
            <input v-model="form.memberNo" />
          </label>
        </template>
        <label>
          开始日期
          <input v-model="form.startDate" type="date" :required="showLeaveDates" />
        </label>
        <label>
          结束日期
          <input v-model="form.endDate" type="date" :required="showLeaveDates" />
        </label>
        <label v-if="isSeal" class="span-2 row">
          <input v-model="form.offlineHandoff" type="checkbox" />
          <span>内容涉密，转线下审批（须在说明中备注）</span>
        </label>
        <label class="span-2">
          附件
          <input type="file" multiple @change="onFiles" />
          <span class="muted" v-if="isSeal">盖章申请附件必传</span>
          <span class="muted" v-else-if="form.files.length">已选择/保留 {{ form.files.length }} 个附件</span>
        </label>
        <div class="span-2 row">
          <button type="button" @click="saveDraft">保存草稿</button>
          <button type="button" @click="previewDocument">预览证明</button>
          <button class="primary">提交审批</button>
          <button type="button" @click="resetForm">新建</button>
        </div>
      </form>
      <iframe v-if="previewHtml" class="card" style="width:100%;min-height:320px;margin-top:12px;border:1px solid #ddd" :srcdoc="previewHtml" title="申请预览"></iframe>
    </section>

    <section>
      <div class="section-title">我的申请</div>
      <div class="stack">
        <article v-for="item in applications" :key="item.id" class="card">
          <div class="row between">
            <strong>{{ item.type }} · {{ item.subtype }}</strong>
            <span class="tag">{{ item.status }}</span>
          </div>
          <p>{{ item.form?.reason }}</p>
          <p class="muted">
            {{ formatTime(item.createdAt) }}
            <span v-if="item.teacherComment"> · {{ item.teacherComment }}</span>
          </p>
          <div class="row wrap">
            <button @click="openDetail(item)">查看详情</button>
            <button @click="downloadDocument(item, 'pdf')">PDF</button>
            <button @click="downloadDocument(item, 'doc')">Word</button>
            <button
              v-if="[APPROVAL.DRAFT, APPROVAL.REJECTED].includes(item.status)"
              class="primary"
              @click="fillForm(item)"
            >
              {{ item.status === APPROVAL.REJECTED ? "修改后重提" : "继续编辑" }}
            </button>
          </div>
        </article>
        <div v-if="!applications.length" class="empty card">暂无申请</div>
      </div>
    </section>
  </div>

  <section v-if="selected" class="card">
    <div class="row between">
      <h3>申请详情</h3>
      <span class="tag">{{ selected.status }}</span>
    </div>
    <p>{{ selected.type }} · {{ selected.subtype }} · {{ selected.id }}</p>
    <p class="muted">说明：{{ selected.form?.reason || "未填写" }}</p>
    <button @click="downloadDocument(selected, 'pdf')">下载 PDF 证明</button>
    <button @click="downloadDocument(selected, 'doc')">下载 Word</button>
    <div v-if="selected.attachments?.length" class="section-title">附件</div>
    <div v-if="selected.attachments?.length" class="stack">
      <div v-for="file in selected.attachments" :key="file.id || file.name" class="card row between">
        <span>{{ file.name }} <span class="muted">({{ file.size || 0 }} bytes)</span></span>
        <button @click="downloadAttachment(file)">下载</button>
      </div>
    </div>
    <div class="section-title">审批轨迹</div>
    <div class="stack">
      <div v-for="row in selected.auditTrail || []" :key="`${row.at}-${row.action}`" class="card muted">
        {{ formatTime(row.at) }} · {{ row.actor }} · {{ row.action }}
        <span v-if="row.remark"> · {{ row.remark }}</span>
      </div>
    </div>
  </section>
</template>
