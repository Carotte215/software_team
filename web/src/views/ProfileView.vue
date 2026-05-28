<script setup>
import { inject, onMounted, reactive, ref } from "vue";

const api = inject("api");
const toast = inject("toast");
const student = ref(null);
const pwdForm = reactive({ oldPassword: "", newPassword: "", confirm: "" });
const extForm = reactive({ competitions: "", volunteerHours: "", research: "", practice: "" });
const savingExt = ref(false);

onMounted(load);

async function load() {
  student.value = await api.getCurrentStudent();
  const ext = student.value?.extension || {};
  Object.assign(extForm, {
    competitions: ext.competitions || "",
    volunteerHours: ext.volunteerHours ?? "",
    research: ext.research || "",
    practice: ext.practice || "",
  });
}

async function changePassword() {
  if (pwdForm.newPassword.length < 6) {
    toast("新密码至少 6 位");
    return;
  }
  if (pwdForm.newPassword !== pwdForm.confirm) {
    toast("两次输入的新密码不一致");
    return;
  }
  try {
    await api.changePassword({ oldPassword: pwdForm.oldPassword, newPassword: pwdForm.newPassword });
    toast("密码已修改");
    Object.assign(pwdForm, { oldPassword: "", newPassword: "", confirm: "" });
  } catch (error) {
    toast(error.message || "密码修改失败，请检查当前密码");
  }
}

async function saveExtension() {
  savingExt.value = true;
  try {
    const extension = {
      competitions: extForm.competitions.trim(),
      research: extForm.research.trim(),
      practice: extForm.practice.trim(),
    };
    if (extForm.volunteerHours !== "" && extForm.volunteerHours != null) {
      extension.volunteerHours = Number(extForm.volunteerHours) || 0;
    }
    student.value = await api.updateMyProfile({ extension });
    toast("扩展画像已保存");
  } finally {
    savingExt.value = false;
  }
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
      <div class="kv"><div class="k">导师</div><div>{{ student.tutor || "—" }}</div></div>
    </section>

    <section class="card stack">
      <h3>扩展画像（自维护）</h3>
      <p class="muted">可填写竞赛、科研、实践与志愿时长；保存后写入个人 extension 字段。</p>
      <form class="stack" @submit.prevent="saveExtension">
        <input v-model="extForm.competitions" placeholder="竞赛经历" />
        <input v-model="extForm.research" placeholder="科研/项目经历" />
        <input v-model="extForm.practice" placeholder="社会实践" />
        <input v-model="extForm.volunteerHours" type="number" min="0" placeholder="志愿时长（小时）" />
        <button class="primary" :disabled="savingExt">保存扩展信息</button>
      </form>

      <h3>修改密码</h3>
      <form class="stack" @submit.prevent="changePassword">
        <input v-model="pwdForm.oldPassword" type="password" placeholder="当前密码" required />
        <input v-model="pwdForm.newPassword" type="password" placeholder="新密码（≥6位）" required />
        <input v-model="pwdForm.confirm" type="password" placeholder="确认新密码" required />
        <button class="primary">保存新密码</button>
      </form>
    </section>
  </div>
</template>
