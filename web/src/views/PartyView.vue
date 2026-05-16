<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const flow = ref(null);

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
}

async function markDone(taskId) {
  await api.completePartyTask(taskId);
  toast("已记录完成");
  await load();
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
  </template>
</template>
