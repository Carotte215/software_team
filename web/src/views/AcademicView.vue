<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { ROLES } from "../data/seed.js";
import { go } from "../state/routes.js";

const api = inject("api");
const toast = inject("toast");
const session = inject("session");
const report = ref(null);
const planPayload = ref(null);
const lastTranscriptFile = ref(null);

const isStudent = computed(() => session.value.role === ROLES.STUDENT);

onMounted(load);

async function load() {
  try {
    const [reportRes, planRes] = await Promise.all([
      api.getAcademicReport(),
      api.getAcademicPlan(),
    ]);
    report.value = reportRes;
    planPayload.value = planRes;
  } catch (error) {
    report.value = { ok: false, message: error.message || "学业数据加载失败" };
    planPayload.value = null;
  }
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
  try {
    await api.saveAcademicProgress(modules);
    toast("已保存学业数据");
    await load();
  } catch (error) {
    toast(error.message || "学业数据保存失败");
  }
}

const parsePreview = ref(null);

async function uploadTranscript(event) {
  const file = event?.target?.files?.[0];
  if (!file) {
    toast("请选择 PDF 成绩单");
    return;
  }
  lastTranscriptFile.value = file;
  try {
    const result = await api.uploadTranscriptFile(file, false);
    parsePreview.value = result;
    toast(result.message || (result.ok ? "已解析，请确认后写入学分" : "解析失败"));
    if (result.ok && !result.needsConfirm) await load();
  } catch (error) {
    parsePreview.value = null;
    toast(error.message || "成绩单解析失败");
  }
}

async function confirmParsedCredits() {
  if (!parsePreview.value?.ok) return;
  const file = lastTranscriptFile.value;
  if (!file) {
    toast("请重新选择 PDF 文件后确认");
    return;
  }
  try {
    const result = await api.uploadTranscriptFile(file, true);
    parsePreview.value = null;
    lastTranscriptFile.value = null;
    toast(result.message || "学分已更新");
    await load();
  } catch (error) {
    toast(error.message || "学分写入失败");
  }
}
</script>

<template>
  <div v-if="!isStudent" class="card">
    <p>管理端请在工作台查看<strong>学业风险名单</strong>（按培养方案缺口排序）。</p>
    <button class="primary" @click="go('workbench')">前往工作台</button>
  </div>

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
          <p class="muted">
            识别 {{ parsePreview.courseCount || parsePreview.courses?.length || 0 }} 门课程
            <span v-if="parsePreview.parseSource"> · 来源 {{ parsePreview.parseSource.toUpperCase() }}</span>
          </p>
          <div v-if="parsePreview.warnings?.length" class="stack">
            <div v-for="(warning, i) in parsePreview.warnings" :key="`warning-${i}`" class="tag orange">{{ warning }}</div>
          </div>
          <div v-if="parsePreview.courses?.length" class="stack">
            <div v-for="(c, i) in parsePreview.courses.slice(0, 8)" :key="i" class="muted">{{ c.name }} · {{ c.credit }} 学分 · {{ c.category }}</div>
          </div>
          <div v-if="parsePreview.suggestedModules?.length" class="stack">
            <div class="muted">建议写入模块：</div>
            <div v-for="item in parsePreview.suggestedModules" :key="item.key" class="muted">{{ item.key }} · 已识别 {{ item.earned }} 学分</div>
          </div>
          <button type="button" class="primary" @click="confirmParsedCredits">确认写入模块学分</button>
        </div>
        <div v-else-if="parsePreview && !parsePreview.ok" class="card stack">
          <div class="tag orange">解析失败</div>
          <p class="muted">{{ parsePreview.message || "未能识别课程数据" }}</p>
          <div v-for="(warning, i) in parsePreview.warnings || []" :key="`fail-${i}`" class="muted">{{ warning }}</div>
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

  <div v-else-if="isStudent" class="card">
    <div>{{ report?.message || "加载中" }}</div>
    <div v-if="report?.hint" class="muted">{{ report.hint }}</div>
  </div>

  <div class="section-title">修读建议</div>
  <div class="stack">
    <div v-for="item in report?.suggestions || []" :key="item.focus" class="card">{{ item.hint }}</div>
  </div>
</template>
