<script setup>
import { inject, onMounted, reactive, ref, watch } from "vue";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const tab = ref("search");
const query = reactive({ q: "", category: "全部" });
const list = ref([]);
const categories = ref(["全部"]);
const templates = ref([]);
const expanded = ref(null);
const previewUrl = ref("");
const favoriteIds = ref(new Set());
const searchMeta = ref(null);

onMounted(load);

async function load() {
  if (tab.value === "search") {
    const res = await api.searchKnowledge(query);
    list.value = res.list || [];
    searchMeta.value = res.searchMeta || null;
    categories.value = res.categories || ["全部"];
    templates.value = res.templates || [];
    if (query.q.trim() && list.value.length === 0) {
      await api.recordKnowledgeMiss(query.q.trim());
    }
  } else if (tab.value === "favorites") {
    list.value = (await api.listKnowledgeFavorites().catch(() => ({ list: [] }))).list || [];
  } else if (tab.value === "recent") {
    list.value = (await api.listKnowledgeRecent().catch(() => ({ list: [] }))).list || [];
  } else if (tab.value === "trending") {
    list.value = (await api.listKnowledgeTrending().catch(() => ({ list: [] }))).list || [];
  }
  const fav = await api.listKnowledgeFavorites().catch(() => ({ list: [] }));
  favoriteIds.value = new Set((fav.list || []).map((item) => item.id));
}

watch(tab, load);

async function expandItem(item) {
  expanded.value = await api.getKnowledge(item.id).catch(() => item);
  if (expanded.value?.favorited) favoriteIds.value.add(item.id);
}

async function toggleFavorite(item) {
  try {
    const res = favoriteIds.value.has(item.id)
      ? await api.removeKnowledgeFavorite(item.id)
      : await api.toggleKnowledgeFavorite(item.id);
    if (res.favorited) favoriteIds.value.add(item.id);
    else favoriteIds.value.delete(item.id);
    toast(res.favorited ? "已收藏" : "已取消收藏");
    if (tab.value === "favorites") await load();
  } catch (error) {
    toast(error.message || "收藏操作失败");
  }
}

function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

async function downloadTemplate(item) {
  try {
    const blob = await api.downloadTemplate(item);
    saveBlob(blob, `${item.name}.${item.format || "txt"}`);
    toast("模板下载已开始");
  } catch (error) {
    toast(error.message || "模板暂未上传，请联系管理员先维护模板文件");
  }
}

async function downloadAttachment(file) {
  try {
    const blob = await api.downloadFile(file);
    saveBlob(blob, file.name || "policy-attachment");
    toast("附件下载已开始");
  } catch (error) {
    toast(error.message || "附件下载失败");
  }
}

async function previewAttachment(file) {
  try {
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = await api.previewFile(file);
  } catch (error) {
    toast("该文件类型暂不支持在线预览，请下载查看");
  }
}
</script>

<template>
  <div class="toolbar row wrap">
    <button :class="{ primary: tab === 'search' }" @click="tab = 'search'">搜索</button>
    <button :class="{ primary: tab === 'favorites' }" @click="tab = 'favorites'">我的收藏</button>
    <button :class="{ primary: tab === 'recent' }" @click="tab = 'recent'">最近浏览</button>
    <button :class="{ primary: tab === 'trending' }" @click="tab = 'trending'">热门政策</button>
  </div>

  <form v-if="tab === 'search'" class="toolbar" @submit.prevent="load">
    <input v-model="query.q" placeholder="输入关键词，如：奖助学金、宿舍、休学" />
    <select v-model="query.category" @change="load">
      <option v-for="item in categories" :key="item">{{ item }}</option>
    </select>
    <button class="primary">搜索</button>
  </form>

  <div class="grid cols-2">
    <section>
      <div class="section-title">政策条目</div>
      <div v-if="list.length" class="stack">
        <article v-for="item in list" :key="item.id" class="card">
          <div class="row between">
            <h3 class="item-title">{{ item.title }}</h3>
            <span class="tag">{{ item.category }}</span>
          </div>
          <p>{{ item.summary }}</p>
          <p v-if="item.matchReason" class="muted">{{ item.matchReason }}</p>
          <p>
            <span v-for="tag in item.tags" :key="tag" class="tag gray">{{ tag }}</span>
          </p>
          <p class="muted">更新：{{ formatTime(item.updatedAt) }} · 阅读 {{ item.hitCount || 0 }}</p>
          <p v-if="item.sensitiveHint" class="muted">敏感内容仅展示摘要，请走官方渠道。</p>
          <p v-if="item.officialLink">
            <a :href="item.officialLink" target="_blank" rel="noopener">官方说明链接</a>
          </p>
          <div class="row wrap">
            <button @click="expandItem(item)">查看详情</button>
            <button @click="toggleFavorite(item)">{{ favoriteIds.has(item.id) ? "取消收藏" : "收藏" }}</button>
            <button v-for="file in item.attachments || []" :key="file.id || file.name" @click="downloadAttachment(file)">
              下载 {{ file.name }}
            </button>
            <button v-for="file in item.attachments || []" :key="`${file.id}-preview`" @click="previewAttachment(file)">
              预览 {{ file.name }}
            </button>
          </div>
        </article>
      </div>
      <div v-else-if="searchMeta?.noResult" class="card stack">
        <p>{{ searchMeta.hint }}</p>
        <p class="muted">关键词「{{ searchMeta.keyword }}」已记录至工作台「未命中词」，供管理员补充知识库。</p>
      </div>
      <div v-else class="empty card">输入关键词开始检索政策与办事说明。</div>
    </section>

    <section>
      <div class="section-title">常用模板</div>
      <div class="stack">
        <div v-for="item in templates" :key="item.id" class="card row between">
          <div>
            <strong>{{ item.name }}</strong>
            <div class="muted">{{ item.scene }} · {{ item.format }}</div>
          </div>
          <button @click="downloadTemplate(item)">下载</button>
        </div>
      </div>
      <div v-if="expanded" class="card" style="margin-top:16px">
        <h3>{{ expanded.title }}</h3>
        <pre style="white-space:pre-wrap">{{ expanded.body || expanded.summary }}</pre>
        <iframe v-if="previewUrl" :src="previewUrl" title="附件预览" style="width:100%;min-height:360px;margin-top:12px;border:1px solid #ddd"></iframe>
      </div>
    </section>
  </div>
</template>
