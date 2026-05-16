<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const flow = ref(null);
const theory = ref({ list: [] });
const theoryAnswers = ref({});
const theoryResult = ref(null);

const current = computed(() => {
  if (!flow.value) return null;
  return flow.value.stages.find((item) => item.key === flow.value.currentKey);
});
const currentRule = computed(() => {
  if (!flow.value) return null;
  return flow.value.timelineRules?.find((item) => item.stageKey === flow.value.currentKey);
});

onMounted(load);

async function load() {
  flow.value = await api.getPartyProgress();
  theory.value = await api.listTheoryQuestions().catch(() => ({ list: [] }));
}

async function markDone(taskId) {
  await api.completePartyTask(taskId);
  toast("已记录完成");
  await load();
}

async function submitTheory() {
  theoryResult.value = await api.submitTheoryAttempt(theoryAnswers.value);
  toast(`理论自测得分 ${theoryResult.value.score}`);
}
</script>

<template>
  <template v-if="flow">
    <div class="card">
      <h3>{{ flow.flowName }}</h3>
      <p class="muted">当前阶段：<strong>{{ current?.name }}</strong>。提醒任务后续可接微信订阅消息或邮件。</p>
      <p v-if="currentRule" class="muted">
        标准周期 {{ currentRule.durationDays }} 天，提前 {{ currentRule.remindBeforeDays }} 天提醒；材料要求：{{ currentRule.material }}
      </p>
    </div>

    <div class="grid cols-2">
      <section>
        <div class="section-title">流程总览</div>
        <div class="card timeline">
          <div
            v-for="stage in flow.stages"
            :key="stage.key"
            class="step"
            :class="{ done: stage.order < current?.order, current: stage.key === flow.currentKey }"
          >
            <div class="dot"></div>
            <div>
              <div class="step-name">{{ stage.name }}</div>
              <div class="muted">{{ stage.desc }}</div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div class="section-title">待办提醒</div>
        <div class="stack">
          <div v-for="task in flow.tasks" :key="task.id" class="card">
            <strong>{{ task.title }}</strong>
            <p class="muted">{{ task.body }}</p>
            <p>建议完成：{{ formatTime(task.dueAt) }}</p>
            <button class="primary" :disabled="task.done" @click="markDone(task.id)">
              {{ task.done ? "已完成" : "标记完成" }}
            </button>
          </div>
          <div v-if="!flow.tasks.length" class="empty card">暂无待办</div>
        </div>

        <div class="section-title">历史节点</div>
        <div class="stack">
          <div v-for="row in flow.history" :key="row.at" class="card">
            <strong>{{ flow.stages.find((s) => s.key === row.stageKey)?.name || row.stageKey }}</strong>
            <div class="muted">{{ formatTime(row.at) }} · {{ row.remark }}</div>
          </div>
        </div>
      </section>
    </div>

    <section class="card">
      <div class="row between">
        <h3>理论自测</h3>
        <span v-if="theory.latestAttempt" class="tag gray">上次 {{ theory.latestAttempt.score }} 分</span>
      </div>
      <form class="stack" @submit.prevent="submitTheory">
        <article v-for="question in theory.list" :key="question.id" class="card">
          <strong>{{ question.stem }}</strong>
          <div class="row wrap">
            <label v-for="option in question.options" :key="option" class="row">
              <input v-model="theoryAnswers[question.id]" type="radio" :name="question.id" :value="option" />
              {{ option }}
            </label>
          </div>
        </article>
        <button class="primary" :disabled="!theory.list.length">提交自测</button>
      </form>
      <div v-if="theoryResult" class="stack">
        <p class="muted">本次得分 {{ theoryResult.score }}，答对 {{ theoryResult.correct }}/{{ theoryResult.total }}</p>
        <div v-for="item in theoryResult.details" :key="item.id" class="card">
          <strong>{{ item.correct ? "正确" : "需复习" }} · {{ item.stem }}</strong>
          <p class="muted">你的答案：{{ item.answer || "未作答" }} · 正确答案：{{ item.correctAnswer }}</p>
          <p>{{ item.explanation }}</p>
        </div>
      </div>
    </section>
  </template>
</template>
