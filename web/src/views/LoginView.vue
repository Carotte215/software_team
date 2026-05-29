<script setup>
import { inject, ref } from "vue";
import { go } from "../state/routes.js";
import { setSession } from "../state/session.js";
import { canAccessRoute } from "../state/routes.js";

const api = inject("api");
const session = inject("session");
const toast = inject("toast");

const loginForm = ref({ studentId: session.value.studentId || "", password: "" });
const loginBusy = ref(false);

async function loginRemote() {
  loginBusy.value = true;
  try {
    const result = await api.login(loginForm.value);
    setSession({ studentId: result.studentId, role: result.role, token: result.token });
    if (!canAccessRoute("home", result.role)) {
      go("home"); // The App.vue watcher will handle redirecting to a visible route or home
    } else {
      go("home");
    }
    toast("登录成功");
  } catch (error) {
    toast("登录失败，请检查身份与口令");
  } finally {
    loginBusy.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card card">
      <div class="login-header">
        <h1 class="page-title">登录</h1>
        <p class="muted">学院学生综合服务与党团管理平台</p>
      </div>
      <div class="stack">
        <div class="form-item">
          <input v-model="loginForm.studentId" placeholder="请输入学号" @keyup.enter="loginRemote" />
        </div>
        <div class="form-item">
          <input v-model="loginForm.password" type="password" placeholder="请输入登录密码" @keyup.enter="loginRemote" />
        </div>
        <button class="primary login-btn" :disabled="loginBusy" @click="loginRemote">
          {{ loginBusy ? "登录中..." : "登录" }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 30px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header .page-title {
  margin-bottom: 10px;
  justify-content: center;
  display: flex;
}

.login-header .page-title::before {
  display: none;
}

.login-btn {
  width: 100%;
  margin-top: 10px;
  height: 48px;
  font-size: 16px;
}

.form-item {
  margin-bottom: 8px;
}
</style>
