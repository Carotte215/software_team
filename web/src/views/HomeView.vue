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
  ["knowledge", "政策与模板", "政策检索、标准答复、模板材料"],
  ["party", "党团流程", "阶段进度、历史节点、任务提醒"],
  ["apply", "办事申请", "证明 / 请假 / 盖章线上审批"],
  ["notices", "通知公告", "标签分类、定向通知、批次追踪"],
  ["academic", "学业分析", "培养方案比对与风险提示"],
  ["honors", "荣誉展示", "国奖、校优榜样与筛选"],
  ["profile", "个人画像", "基础信息、扩展字段、改密"],
  ["workbench", "管理工作台", "审批、发布、统计、审计日志"],
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
        当前身份：{{ me?.name }} · {{ ROLE_LABEL[session.role] }}。请通过导航办理事务、查看通知并跟进党团流程。
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
