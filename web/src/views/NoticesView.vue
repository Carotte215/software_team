<script setup>
import { inject, onMounted, ref } from "vue";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const notices = ref([]);
const messages = ref([]);

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
          </p>
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
          <button @click="markRead(msg.id)">标记已读</button>
        </div>
      </div>
    </section>
  </div>
</template>
