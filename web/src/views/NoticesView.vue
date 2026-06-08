<script setup>
import { computed, inject, onMounted, ref } from "vue";
import EmptyStateCard from "../components/EmptyStateCard.vue";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const notices = ref([]);
const messages = ref([]);
const expandedNotice = ref(null);
const loadError = ref("");
const selectedTag = ref("");

const availableTags = computed(() => {
  const tags = notices.value.flatMap((item) => item.tags || []);
  return Array.from(new Set(tags)).sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
});

const filteredNotices = computed(() => {
  if (!selectedTag.value) return notices.value;
  return notices.value.filter((item) => (item.tags || []).includes(selectedTag.value));
});

onMounted(load);

async function load() {
  try {
    const [noticeRes, inboxRes] = await Promise.all([
      api.listNotices(),
      api.getInbox(),
    ]);
    notices.value = noticeRes.list || [];
    messages.value = inboxRes.list || [];
    loadError.value = "";
  } catch (error) {
    notices.value = [];
    messages.value = [];
    loadError.value = error.message || "通知加载失败";
  }
}

async function markRead(id) {
  try {
    await api.markMessageRead(id);
    toast("已标记已读");
    await load();
  } catch (error) {
    toast(error.message || "标记已读失败");
  }
}

function toggleNotice(item) {
  expandedNotice.value = expandedNotice.value?.id === item.id ? null : item;
}

function selectTag(tag) {
  selectedTag.value = selectedTag.value === tag ? "" : tag;
  expandedNotice.value = null;
}
</script>

<template>
  <div v-if="loadError" class="card">{{ loadError }}</div>
  <div class="grid cols-2">
    <section>
      <div class="section-title">通知公告</div>
      <div v-if="availableTags.length" class="toolbar row wrap notice-filter">
        <span class="muted">按标签筛选：</span>
        <button class="tag" :class="{ green: !selectedTag }" type="button" @click="selectTag('')">全部</button>
        <button
          v-for="tag in availableTags"
          :key="tag"
          class="tag tag-button"
          :class="{ green: selectedTag === tag }"
          type="button"
          @click="selectTag(tag)"
        >
          {{ tag }}
        </button>
      </div>
      <div class="stack">
        <article v-for="item in filteredNotices" :key="item.id" class="card notice">
          <div class="row between">
            <strong>{{ item.title }}</strong>
            <span class="muted">{{ formatTime(item.publishedAt) }}</span>
          </div>
          <p>{{ item.summary }}</p>
          <p>
            <button
              v-for="tag in item.tags"
              :key="tag"
              class="tag tag-button"
              :class="{ green: selectedTag === tag }"
              type="button"
              @click="selectTag(tag)"
            >
              {{ tag }}
            </button>
            <span class="tag gray">{{ item.source }}</span>
          </p>
          <button @click="toggleNotice(item)">{{ expandedNotice?.id === item.id ? "收起" : "全文" }}</button>
          <p v-if="expandedNotice?.id === item.id" class="muted" style="white-space:pre-wrap">{{ item.content }}</p>
        </article>
        <EmptyStateCard v-if="!filteredNotices.length" :text="selectedTag ? `暂无「${selectedTag}」标签通知` : '暂无通知公告'" />
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
        <EmptyStateCard v-if="!messages.length" text="暂无站内信" />
      </div>
    </section>
  </div>
</template>
