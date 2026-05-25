<script setup>
import { inject, onMounted, ref } from "vue";

const api = inject("api");
const toast = inject("toast");
const report = ref(null);
const planPayload = ref(null);

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

async function uploadTranscript() {
  await api.uploadTranscript({ name: "成绩单.pdf", note: "学生端登记：成绩单文件已提交审核队列" });
  toast("已登记上传记录");
  await load();
}
</script>

<template>
  <div v-if="report?.ok" class="grid cols-2">
    <section>
      <div class="card">
        <h3>综合风险：{{ report.riskLevel }}</h3>
        <p class="muted">系统依据培养方案与已获学分进行比对，展示模块缺口和风险提示。</p>
        <button @click="uploadTranscript">登记成绩单上传</button>
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
