<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <el-card shadow="never">
    <el-empty :description="`${route.meta.title} — 功能开发中`">
      <template #image>
        <span class="placeholder-icon">🚧</span>
      </template>
    </el-empty>
  </el-card>
</template>

<style scoped>
.placeholder-icon {
  font-size: 64px;
}
</style>
