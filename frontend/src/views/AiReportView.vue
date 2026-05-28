<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { generateAiReport, getAiReport, type AiReport } from '@/api/ai'
import { listExperiments } from '@/api/experiment'
import AiReportPanel from '@/components/AiReportPanel.vue'
import { statusLabel } from '@/utils/format'

const route = useRoute()
const experiments = ref<{ id: number; taskNo: string; expName: string; status: string }[]>([])
const selectedId = ref<number | undefined>()
const report = ref<AiReport | null>(null)
const generating = ref(false)

async function loadExperiments() {
  const [c, a] = await Promise.all([
    listExperiments({ status: 'COMPLETED', pageSize: 50 }),
    listExperiments({ status: 'ARCHIVED', pageSize: 50 }),
  ])
  experiments.value = [...c.data.data!.items, ...a.data.data!.items]
  const qid = route.query.experimentId
  if (qid) selectedId.value = Number(qid)
  else if (!selectedId.value && experiments.value.length) {
    selectedId.value = experiments.value[0].id
  }
}

async function loadReport() {
  if (!selectedId.value) return
  try {
    const { data } = await getAiReport(selectedId.value)
    report.value = data.data!
  } catch {
    report.value = null
  }
}

async function onGenerate() {
  if (!selectedId.value) {
    ElMessage.warning('请选择试验任务')
    return
  }
  generating.value = true
  try {
    const { data } = await generateAiReport(selectedId.value)
    report.value = data.data!
    ElMessage.success(data.data!.mock ? '已生成模拟报告' : 'AI 报告生成成功')
  } finally {
    generating.value = false
  }
}

onMounted(async () => {
  await loadExperiments()
  await loadReport()
})
</script>

<template>
  <div>
    <el-card shadow="never" class="toolbar">
      <el-select
        v-model="selectedId"
        placeholder="选择试验任务"
        style="width: 300px"
        @change="loadReport"
      >
        <el-option
          v-for="e in experiments"
          :key="e.id"
          :label="`${e.taskNo} - ${e.expName} (${statusLabel(e.status)})`"
          :value="e.id"
        />
      </el-select>
      <el-button type="primary" :loading="generating" :disabled="!selectedId" @click="onGenerate">
        生成 AI 分析
      </el-button>
      <el-button :disabled="!selectedId" @click="loadReport">刷新</el-button>
    </el-card>

    <el-alert
      class="tip"
      type="info"
      :closable="false"
      show-icon
      title="说明"
      description="默认使用本地模拟报告（MOCK_AI=true）。在 backend/.env 中配置 DEEPSEEK_API_KEY 并设置 MOCK_AI=false 可调用真实 DeepSeek API。"
    />

    <AiReportPanel :report="report" :loading="generating" />
  </div>
</template>

<style scoped>
.toolbar :deep(.el-card__body) {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.tip {
  margin: 16px 0;
}
</style>
