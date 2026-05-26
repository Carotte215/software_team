<script setup>
import { inject, onMounted, ref } from "vue";

const api = inject("api");
const toast = inject("toast");
const report = ref(null);
const planPayload = ref(null);
const lastTranscriptFile = ref(null);

onMounted(load);

async function load() {
  const [reportRes, planRes] = await Promise.all([
    api.getAcademicReport(),
    api.getAcademicPlan(),
  ]);
  report.value = reportRes;
  planPayload.value = planRes;
}

function earnedFor(key) {
  return planPayload.value?.progress?.modules?.find((item) => item.key === key)?.earned || 0;
}

async function saveProgress(event) {
  const form = new FormData(event.target);
  const modules = (planPayload.value?.plan?.modules || []).map((item) => ({
    key: item.key,
    earned: Number(form.get(item.key) || 0),
  }));
  await api.saveAcademicProgress(modules);
  toast("已保存学业数据");
  await load();
}

const parsePreview = ref(null);

async function uploadTranscript(event) {
  const file = event?.target?.files?.[0];
  if (!file) {
    toast("请选择 PDF 成绩单");
    return;
  }
  lastTranscriptFile.value = file;
  const result = await api.uploadTranscriptFile(file, false);
  parsePreview.value = result;
  toast(result.message || (result.ok ? "已解析，请确认后写入学分" : "解析失败"));
  if (result.ok && !result.needsConfirm) await load();
}

async function confirmParsedCredits() {
  if (!parsePreview.value?.ok) return;
  const file = lastTranscriptFile.value;
  if (!file) {
    toast("请重新选择 PDF 文件后确认");
    return;
  }
  const result = await api.uploadTranscriptFile(file, true);
  parsePreview.value = null;
  lastTranscriptFile.value = null;
  toast(result.message || "学分已更新");
  await load();
}
</script>

<template>
  <div v-if="report?.ok" class="grid cols-2">
    <section>
      <div class="card">
        <h3>综合风险：{{ report.riskLevel }}</h3>
        <p class="muted">系统依据培养方案与已获学分进行比对，展示模块缺口和风险提示。</p>
        <label class="stack">
          上传 PDF 成绩单
          <input type="file" accept=".pdf" @change="uploadTranscript" />
        </label>
        <div v-if="parsePreview?.ok" class="card stack">
          <p class="muted">识别 {{ parsePreview.courseCount || parsePreview.courses?.length || 0 }} 门课程</p>
          <div v-if="parsePreview.courses?.length" class="stack">
            <div v-for="(c, i) in parsePreview.courses.slice(0, 8)" :key="i" class="muted">{{ c.name }} · {{ c.credit }} 学分 · {{ c.category }}</div>
          </div>
          <button type="button" class="primary" @click="confirmParsedCredits">确认写入模块学分</button>
        </div>
        <p v-if="report.warning" class="tag orange">{{ report.warning }}</p>
      </div>

      <div class="section-title">模块学分缺口</div>
      <div class="stack">
        <div v-for="item in report.modules" :key="item.key" class="card row between">
          <div>
            <strong>{{ item.name }}</strong>
            <div class="muted">要求 {{ item.required }} · 已获 {{ item.earned }} · 缺口 {{ item.gap }}</div>
          </div>
          <span class="tag" :class="item.risk === '高' ? 'orange' : 'green'">风险 {{ item.risk }}</span>
        </div>
      </div>
    </section>

    <section class="card">
      <h3>维护已获学分</h3>
      <form class="stack" @submit.prevent="saveProgress">
        <label v-for="item in planPayload?.plan?.modules || []" :key="item.key">
          {{ item.name }}（要求 {{ item.required }}）
          <input type="number" min="0" step="0.5" :name="item.key" :value="earnedFor(item.key)" />
        </label>
        <button class="primary">保存</button>
      </form>
    </section>
  </div>

  <div v-else class="card">{{ report?.message || "加载中" }}</div>

  <div class="section-title">修读建议</div>
  <div class="stack">
    <div v-for="item in report?.suggestions || []" :key="item.focus" class="card">{{ item.hint }}</div>
  </div>
</template>
