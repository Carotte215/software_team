<script setup>
import { inject, onMounted, reactive, ref } from "vue";
import { formatTime } from "../utils.js";

const api = inject("api");
const toast = inject("toast");
const applications = ref([]);
const form = reactive({
  type: "证明申请",
  subtype: "在读证明",
  reason: "",
  startDate: "",
  endDate: "",
  files: [],
});

onMounted(load);

async function load() {
  const res = await api.listApplications();
  applications.value = res.list || [];
}

function onFiles(event) {
  form.files = Array.from(event.target.files || []);
}

async function submit() {
  if (!form.reason.trim()) {
    toast("请填写申请说明");
    return;
  }
  if (form.type === "盖章申请" && form.files.length === 0) {
    toast("盖章申请须上传附件");
    return;
  }
  await api.submitApplication({
    type: form.type,
    subtype: form.subtype,
    form: {
      reason: form.reason,
      startDate: form.startDate,
      endDate: form.endDate,
    },
    attachments: form.files.map((file) => ({ name: file.name, size: file.size })),
  });
  Object.assign(form, { reason: "", startDate: "", endDate: "", files: [] });
  toast("已提交审批");
  await load();
}
</script>

<template>
  <div class="grid cols-2">
    <section class="card">
      <h3>发起办事申请</h3>
      <form class="form-grid" @submit.prevent="submit">
        <label>
          申请类型
          <select v-model="form.type">
            <option>证明申请</option>
            <option>请假申请</option>
            <option>盖章申请</option>
          </select>
        </label>
        <label>
          子类
          <input v-model="form.subtype" />
        </label>
        <label class="span-2">
          申请说明
          <textarea v-model="form.reason" placeholder="请填写事由；涉密内容请备注并转线下流程"></textarea>
        </label>
        <label>
          开始日期
          <input v-model="form.startDate" type="date" />
        </label>
        <label>
          结束日期
          <input v-model="form.endDate" type="date" />
        </label>
        <label class="span-2">
          附件
          <input type="file" multiple @change="onFiles" />
        </label>
        <div class="span-2 row">
          <button class="primary">提交审批</button>
        </div>
      </form>
    </section>

    <section>
      <div class="section-title">我的申请</div>
      <div class="stack">
        <article v-for="item in applications" :key="item.id" class="card">
          <div class="row between">
            <strong>{{ item.type }} · {{ item.subtype }}</strong>
            <span class="tag">{{ item.status }}</span>
          </div>
          <p>{{ item.form?.reason }}</p>
          <p class="muted">
            {{ formatTime(item.createdAt) }}
            <span v-if="item.teacherComment"> · {{ item.teacherComment }}</span>
          </p>
        </article>
        <div v-if="!applications.length" class="empty card">暂无申请</div>
      </div>
    </section>
  </div>
</template>
