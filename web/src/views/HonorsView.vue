<script setup>
import { inject, onMounted, reactive, ref } from "vue";

const api = inject("api");
const filter = reactive({ major: "", category: "" });
const honors = ref([]);

onMounted(load);

async function load() {
  const data = Object.fromEntries(Object.entries(filter).filter(([, value]) => value));
  const res = await api.listHonors(data);
  honors.value = res.list || [];
}
</script>

<template>
  <form class="toolbar" @submit.prevent="load">
    <input v-model="filter.major" placeholder="专业关键词" />
    <select v-model="filter.category">
      <option value="">全部类别</option>
      <option>国家级</option>
      <option>校级</option>
      <option>省部级</option>
    </select>
    <button class="primary">筛选</button>
  </form>

  <div class="grid cols-3">
    <article v-for="item in honors" :key="item.id" class="card">
      <h3>{{ item.title }}</h3>
      <p>{{ item.winner }} · {{ item.grade }} · {{ item.major }}</p>
      <p>
        <span class="tag">{{ item.year }}</span>
        <span class="tag green">{{ item.category }}</span>
      </p>
      <p class="muted">{{ item.intro }}</p>
    </article>
  </div>
</template>
