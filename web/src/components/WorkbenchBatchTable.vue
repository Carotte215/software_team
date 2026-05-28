<script setup>
import { formatTime } from "../utils.js";

defineProps({
  batches: {
    type: Array,
    default: () => [],
  },
  batchFilter: {
    type: Object,
    required: true,
  },
  canDispatch: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["apply-filter", "dispatch-scheduled"]);
</script>

<template>
  <div class="row between">
    <div class="section-title">批次统计</div>
    <div class="row wrap">
      <input v-model="batchFilter.title" placeholder="标题筛选" />
      <input v-model="batchFilter.batchId" placeholder="批次号" />
      <select v-model="batchFilter.status">
        <option value="">全部状态</option>
        <option value="sent">已发送</option>
        <option value="scheduled">待发送</option>
      </select>
      <button @click="$emit('apply-filter')">筛选</button>
      <button v-if="canDispatch" class="primary" @click="$emit('dispatch-scheduled')">派发到期</button>
    </div>
  </div>
  <div v-if="batches.length" class="table-wrap">
    <table class="table">
      <thead>
        <tr><th>批次</th><th>状态</th><th>渠道</th><th>发送/失败</th><th>送达/失败</th><th>已读</th><th>可观测性</th></tr>
      </thead>
      <tbody>
        <template v-for="batch in batches" :key="batch.id">
          <tr v-for="channel in batch.channels" :key="`${batch.id}-${channel.name}`">
            <td>
              {{ batch.title }}<br />
              <span class="muted">{{ batch.id }}</span>
              <span v-if="batch.scheduledAt" class="muted"><br />{{ formatTime(batch.scheduledAt) }}</span>
            </td>
            <td><span class="tag" :class="batch.status === 'scheduled' ? 'orange' : 'green'">{{ batch.status === "scheduled" ? "待发送" : "已发送" }}</span></td>
            <td>{{ channel.name }}</td>
            <td>{{ channel.sendOk }}/{{ channel.sendFail }}</td>
            <td>{{ channel.deliverOk }}/{{ channel.deliverFail }}</td>
            <td>{{ channel.read }}</td>
            <td>{{ channel.observability || "可观测" }}</td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
  <div v-else class="empty card">暂无通知批次</div>
</template>
