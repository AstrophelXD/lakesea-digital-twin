<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
const analysisType = ref('OVERVIEW')
const step = ref(1)

const analysisOptions = [
  { value: 'OVERVIEW', label: '试验概况摘要' },
  { value: 'ANOMALY', label: '异常原因分析' },
  { value: 'RISK', label: '风险提示' },
  { value: 'SUGGESTION', label: '后续试验建议' },
]

const selectedExp = computed(() =>
  experiments.value.find((e) => e.id === selectedId.value),
)

const modeLabel = computed(() => {
  if (!report.value) return '—'
  return report.value.analysisMode || (report.value.mock ? 'Mock' : 'DeepSeek API')
})

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
    step.value = 6
  } catch {
    report.value = null
    step.value = selectedId.value ? 2 : 1
  }
}

async function onGenerate() {
  if (!selectedId.value) {
    ElMessage.warning('请选择试验任务')
    return
  }
  generating.value = true
  step.value = 4
  try {
    const { data } = await generateAiReport(selectedId.value, analysisType.value)
    report.value = data.data!
    step.value = 6
    ElMessage.success(data.data!.mock ? '已生成 Mock 报告' : 'AI 报告生成成功')
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
    <el-card shadow="never" class="workflow-card">
      <template #header>AI 报告生成工作流</template>
      <el-steps :active="step" finish-status="success" align-center>
        <el-step title="选择试验" />
        <el-step title="汇总数据" />
        <el-step title="选择类型" />
        <el-step title="生成报告" />
        <el-step title="结构化展示" />
        <el-step title="保存入库" />
      </el-steps>
    </el-card>

    <el-card shadow="never" class="toolbar">
      <el-select
        v-model="selectedId"
        placeholder="1. 选择试验任务"
        style="width: 300px"
        @change="() => { step = 2; loadReport() }"
      >
        <el-option
          v-for="e in experiments"
          :key="e.id"
          :label="`${e.taskNo} - ${e.expName} (${statusLabel(e.status)})`"
          :value="e.id"
        />
      </el-select>

      <el-select v-model="analysisType" placeholder="3. 分析类型" style="width: 180px">
        <el-option
          v-for="opt in analysisOptions"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>

      <el-button type="primary" :loading="generating" :disabled="!selectedId" @click="onGenerate">
        4. 生成报告
      </el-button>
      <el-button :disabled="!selectedId" @click="loadReport">刷新</el-button>

      <el-tag type="info">当前模式：{{ modeLabel }}</el-tag>
    </el-card>

    <el-card v-if="selectedExp" shadow="never" class="summary-card">
      <template #header>2. 试验关键数据摘要</template>
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="任务单号">{{ selectedExp.taskNo }}</el-descriptions-item>
        <el-descriptions-item label="试验名称">{{ selectedExp.expName }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(selectedExp.status) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <AiReportPanel v-if="report" :report="report" />
    <el-empty v-else description="选择试验任务后点击「生成报告」" />
  </div>
</template>

<style scoped>
.workflow-card {
  margin-bottom: 12px;
}
.toolbar {
  margin-bottom: 12px;
}
.toolbar :deep(.el-card__body) {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
.summary-card {
  margin-bottom: 12px;
}
</style>
