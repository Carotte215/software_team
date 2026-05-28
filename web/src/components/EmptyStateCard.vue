<script setup>
defineProps({
  text: {
    type: String,
    default: "暂无数据",
  },
});
</script>

<template>
  <div class="empty card">{{ text }}</div>
</template>
