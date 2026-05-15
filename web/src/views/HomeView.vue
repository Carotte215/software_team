<script setup>
import { inject, onMounted, ref } from "vue";
import { ROLE_LABEL } from "../data/seed.js";
import { go } from "../state/routes.js";
import { formatTime } from "../utils.js";

const api = inject("api");
const session = inject("session");
const notices = ref([]);
const unread = ref(0);
const me = ref(null);

const features = [
  ["knowledge", "政策与模板", "标准答案优先、未命中词沉淀"],
  ["party", "党团流程", "阶段、历史节点、提醒任务"],
  ["apply", "办事申请", "证明 / 请假 / 盖章审批闭环"],
  ["notices", "通知公告", "标签、定向推送、批次统计"],
  ["academic", "学业分析", "培养方案比对与风险提示"],
  ["workbench", "管理工作台", "审批、发布、统计、日志"],
];

onMounted(load);

async function load() {
  const [noticeRes, inboxRes, student] = await Promise.all([
    api.listNotices(),
    api.getInbox(),
    api.getCurrentStudent(),
  ]);
  notices.value = (noticeRes.list || []).slice(0, 4);
  unread.value = inboxRes.unread || 0;
  me.value = student;
}
</script>

<template>
  <div class="grid cols-2">
    <section class="card hero">
      <h2>一站式学生事务入口</h2>
      <p class="muted">
        当前身份：{{ me?.name }} · {{ ROLE_LABEL[session.role] }}。Web 端已切换为 Vue 3 + Vite 实现。
      </p>
    </section>
    <section class="card">
      <h3>站内消息</h3>
      <p><strong>{{ unread }}</strong> 封未读，多渠道触达口径可在通知页查看。</p>
      <button class="primary" @click="go('notices')">查看消息</button>
    </section>
  </div>

  <div class="section-title">核心功能</div>
  <div class="grid cols-3">
    <button v-for="[id, title, desc] in features" :key="id" class="card" @click="go(id)">
      <strong>{{ title }}</strong>
      <br />
      <span class="muted">{{ desc }}</span>
    </button>
  </div>

  <div class="section-title">近期通知</div>
  <div class="stack">
    <article v-for="item in notices" :key="item.id" class="card notice">
      <div class="row between">
        <strong>{{ item.title }}</strong>
        <span class="muted">{{ formatTime(item.publishedAt) }}</span>
      </div>
      <p>{{ item.summary }}</p>
      <p>
        <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
      </p>
    </article>
  </div>
</template>
