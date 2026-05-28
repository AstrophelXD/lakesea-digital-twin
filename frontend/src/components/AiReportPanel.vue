<script setup lang="ts">
import type { AiReport } from '@/api/ai'

defineProps<{
  report: AiReport | null
  loading?: boolean
}>()
</script>

<template>
  <div v-loading="loading" class="ai-panel">
    <template v-if="report">
      <div class="header">
        <h3>{{ report.reportTitle || '试验分析报告' }}</h3>
        <el-tag v-if="report.mock" type="info" size="small">模拟报告（未调用 DeepSeek）</el-tag>
        <el-tag v-else type="success" size="small">{{ report.modelName }}</el-tag>
        <span class="time">{{ report.generatedTime }}</span>
      </div>
      <el-card shadow="never" class="block">
        <template #header>试验概况与数据摘要</template>
        <div class="text-content">{{ report.summaryText }}</div>
      </el-card>
      <el-card shadow="never" class="block">
        <template #header>异常分析、风险提示与改进建议</template>
        <div class="text-content pre-wrap">{{ report.analysisText }}</div>
      </el-card>
    </template>
    <el-empty v-else description="尚未生成报告，请点击「生成 AI 分析」" />
  </div>
</template>

<style scoped>
.ai-panel {
  min-height: 200px;
}
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.header h3 {
  margin: 0;
  font-size: 18px;
  color: #0f766e;
}
.time {
  font-size: 12px;
  color: #9ca3af;
  margin-left: auto;
}
.block {
  margin-bottom: 12px;
}
.text-content {
  line-height: 1.8;
  color: #374151;
  font-size: 14px;
}
.pre-wrap {
  white-space: pre-wrap;
}
</style>
