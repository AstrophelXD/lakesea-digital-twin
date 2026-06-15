<script setup lang="ts">
import { computed } from 'vue'
import type { AiReport } from '@/api/ai'
import MarkdownContent from '@/components/MarkdownContent.vue'

const props = defineProps<{
  report: AiReport | null
  loading?: boolean
}>()

const sections = computed(() => {
  if (!props.report) return []
  if (props.report.sections?.length) return props.report.sections
  const blocks: { title: string; content: string }[] = []
  if (props.report.summaryText) {
    blocks.push({ title: '试验概况与数据摘要', content: props.report.summaryText })
  }
  if (props.report.analysisText) {
    blocks.push({ title: '异常分析、风险提示与改进建议', content: props.report.analysisText })
  }
  return blocks
})

const modelLabel = computed(() => {
  const name = props.report?.modelName
  if (!name || name === 'mock-local') return 'DeepSeek'
  return name
})
</script>

<template>
  <div v-loading="loading" class="ai-panel">
    <template v-if="report">
      <div class="header">
        <h3>{{ report.reportTitle || '试验分析报告' }}</h3>
        <el-tag v-if="report.analysisTypeLabel" type="primary" size="small">
          {{ report.analysisTypeLabel }}
        </el-tag>
        <el-tag type="success" size="small">{{ modelLabel }}</el-tag>
        <span class="time">{{ report.generatedTime }}</span>
      </div>
      <el-card v-for="(sec, idx) in sections" :key="idx" shadow="never" class="block">
        <template #header>{{ sec.title }}</template>
        <MarkdownContent :content="sec.content" />
      </el-card>
    </template>
    <el-empty v-else description="尚未生成报告，请点击「生成报告」" />
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
  color: var(--app-primary);
}
.time {
  font-size: 12px;
  color: #9ca3af;
  margin-left: auto;
}
.block {
  margin-bottom: 12px;
}
</style>
