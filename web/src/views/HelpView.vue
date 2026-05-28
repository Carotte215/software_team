<script setup>
import { REQUIREMENT_MODULES, OUT_OF_SCOPE } from "../data/requirements.js";
import { go } from "../state/routes.js";
</script>

<template>
  <section class="card">
    <h2>需求追溯（V3.0）</h2>
    <p class="muted">对照《初版需求分析文档 v3.0》的功能模块与 Web 路由，便于验收自测。</p>
  </section>

  <div class="stack">
    <article v-for="mod in REQUIREMENT_MODULES" :key="mod.id" class="card">
      <div class="row between wrap">
        <h3>{{ mod.id }} · {{ mod.name }}</h3>
        <span class="tag gray">优先级 {{ mod.priority }}</span>
      </div>
      <table class="table">
        <thead>
          <tr><th>编号</th><th>说明</th><th>Web 入口</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in mod.items" :key="item.fr">
            <td>{{ item.fr }}</td>
            <td>{{ item.desc }}</td>
            <td><button @click="go(item.route)">{{ item.route }}</button></td>
          </tr>
        </tbody>
      </table>
    </article>
  </div>

  <section class="card">
    <h3>明确不做（Out of Scope）</h3>
    <ul>
      <li v-for="item in OUT_OF_SCOPE" :key="item">{{ item }}</li>
    </ul>
  </section>
</template>
