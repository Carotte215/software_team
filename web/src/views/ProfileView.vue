<script setup>
import { inject, onMounted, ref } from "vue";
import { resetDb } from "../api/store.js";

const api = inject("api");
const toast = inject("toast");
const reloadShell = inject("reloadShell");
const student = ref(null);

onMounted(load);

async function load() {
  student.value = await api.getCurrentStudent();
}

function resetDemo() {
  if (!window.confirm("确定重置 Web 演示数据？")) return;
  resetDb();
  reloadShell();
  toast("已重置");
  load();
}
</script>

<template>
  <div class="grid cols-2" v-if="student">
    <section class="card">
      <h2>{{ student.name }}</h2>
      <div class="kv"><div class="k">学号</div><div>{{ student.studentId }}</div></div>
      <div class="kv"><div class="k">年级专业</div><div>{{ student.grade }} · {{ student.major }}</div></div>
      <div class="kv"><div class="k">班级</div><div>{{ student.className }}</div></div>
      <div class="kv"><div class="k">民族</div><div>{{ student.nation }}</div></div>
      <div class="kv"><div class="k">政治面貌</div><div>{{ student.politicalStatus }}</div></div>
      <div class="kv"><div class="k">手机</div><div>{{ student.phoneMasked || student.phone || "—" }}</div></div>
      <div class="kv"><div class="k">导师</div><div>{{ student.tutor }}</div></div>
    </section>

    <section class="card">
      <h3>扩展画像</h3>
      <pre>{{ JSON.stringify(student.extension || {}, null, 2) }}</pre>
      <p class="muted">字段级权限通过 API 层裁剪；后续可替换为后端字段白名单策略。</p>
      <button class="danger" @click="resetDemo">重置 Web 演示数据</button>
    </section>
  </div>
</template>
