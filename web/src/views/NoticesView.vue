<script setup>
import { inject, onMounted, ref } from "vue";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const notices = ref([]);
const messages = ref([]);
const expandedNotice = ref(null);

onMounted(load);

async function load() {
  const [noticeRes, inboxRes] = await Promise.all([
    api.listNotices(),
    api.getInbox(),
  ]);
  notices.value = noticeRes.list || [];
  messages.value = inboxRes.list || [];
}

async function markRead(id) {
  await api.markMessageRead(id);
  toast("已标记已读");
  await load();
}

function toggleNotice(item) {
  expandedNotice.value = expandedNotice.value?.id === item.id ? null : item;
}
</script>

<template>
  <div class="grid cols-2">
    <section>
      <div class="section-title">通知公告</div>
      <div class="stack">
        <article v-for="item in notices" :key="item.id" class="card notice">
          <div class="row between">
            <strong>{{ item.title }}</strong>
            <span class="muted">{{ formatTime(item.publishedAt) }}</span>
          </div>
          <p>{{ item.summary }}</p>
          <p>
            <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
            <span class="tag gray">{{ item.source }}</span>
          </p>
          <button @click="toggleNotice(item)">{{ expandedNotice?.id === item.id ? "收起" : "全文" }}</button>
          <p v-if="expandedNotice?.id === item.id" class="muted" style="white-space:pre-wrap">{{ item.content }}</p>
        </article>
      </div>
    </section>

    <section>
      <div class="section-title">站内信</div>
      <div class="stack">
        <div v-for="msg in messages" :key="msg.id" class="card">
          <div class="row between">
            <strong>{{ msg.title }}</strong>
            <span class="tag" :class="msg.readAt ? 'gray' : 'orange'">{{ msg.readAt ? "已读" : "未读" }}</span>
          </div>
          <p class="muted">{{ msg.summary }}</p>
          <p v-if="msg.channels?.length" class="muted">
            渠道：
            <span v-for="ch in msg.channels" :key="ch.name" class="tag gray">{{ ch.name }}: {{ ch.state || ch.detail }}</span>
          </p>
          <button @click="markRead(msg.id)" :disabled="Boolean(msg.readAt)">标记已读</button>
        </div>
      </div>
    </section>
  </div>
</template>
