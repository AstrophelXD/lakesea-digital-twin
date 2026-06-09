<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  generateAiReport,
  getAiMode,
  getAiReport,
  getExperimentDataSummary,
  listAiCallLogs,
  type AiCallLog,
  type AiMode,
  type AiReport,
  type ExperimentDataSummary,
} from '@/api/ai'
import { listExperiments } from '@/api/experiment'
import AiReportPanel from '@/components/AiReportPanel.vue'
import { statusLabel } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const experiments = ref<{ id: number; taskNo: string; expName: string; status: string }[]>([])
const selectedId = ref<number | undefined>()
const report = ref<AiReport | null>(null)
const summary = ref<ExperimentDataSummary | null>(null)
const callLogs = ref<AiCallLog[]>([])
const aiMode = ref<AiMode | null>(null)
const generating = ref(false)
const loadingSummary = ref(false)
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
  if (aiMode.value) return aiMode.value.analysisMode
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

async function loadMode() {
  const { data } = await getAiMode()
  aiMode.value = data.data!
}

async function loadSummary() {
  if (!selectedId.value) {
    summary.value = null
    return
  }
  loadingSummary.value = true
  try {
    const { data } = await getExperimentDataSummary(selectedId.value)
    summary.value = data.data!
    step.value = Math.max(step.value, 2)
  } catch {
    summary.value = null
  } finally {
    loadingSummary.value = false
  }
}

async function loadCallLogs() {
  const { data } = await listAiCallLogs({
    experimentId: selectedId.value,
    pageSize: 10,
  })
  callLogs.value = data.data!.items
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

async function onSelectChange() {
  step.value = 2
  await Promise.all([loadSummary(), loadReport(), loadCallLogs()])
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
    await Promise.all([loadCallLogs(), loadMode()])
  } finally {
    generating.value = false
  }
}

function goArchive() {
  if (!selectedId.value) return
  router.push({ name: 'archive', query: { experimentId: String(selectedId.value) } })
}

watch(selectedId, () => {
  if (selectedId.value) onSelectChange()
})

onMounted(async () => {
  await Promise.all([loadExperiments(), loadMode()])
  if (selectedId.value) await onSelectChange()
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
      <el-button :disabled="!selectedId" @click="onSelectChange">刷新</el-button>
      <el-button :disabled="!selectedId" @click="goArchive">跳转归档页</el-button>

      <el-tag type="info">当前模式：{{ modeLabel }}</el-tag>
    </el-card>

    <el-card
      v-if="summary || selectedExp"
      v-loading="loadingSummary"
      shadow="never"
      class="summary-card"
    >
      <template #header>2. 试验关键数据摘要（后端聚合）</template>
      <el-descriptions v-if="summary" :column="3" border size="small">
        <el-descriptions-item label="任务单号">{{ summary.taskNo }}</el-descriptions-item>
        <el-descriptions-item label="试验名称">{{ summary.expName }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(summary.status) }}</el-descriptions-item>
        <el-descriptions-item label="采样点数">{{ summary.pointCount }}</el-descriptions-item>
        <el-descriptions-item label="最大速度">
          {{ summary.maxSpeed != null ? `${summary.maxSpeed.toFixed(2)} m/s` : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="最低电量">
          {{ summary.minBattery != null ? `${summary.minBattery.toFixed(1)}%` : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="最大阻力">
          {{ summary.maxResistance != null ? `${summary.maxResistance.toFixed(1)} N` : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="最大横摇">
          {{ summary.maxRoll != null ? `${summary.maxRoll.toFixed(1)}°` : '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="告警">
          {{ summary.alarmCount }} 条（{{ summary.alarmSummary }}）
        </el-descriptions-item>
      </el-descriptions>
      <el-table
        v-if="summary?.alarms?.length"
        :data="summary.alarms"
        size="small"
        style="margin-top: 12px"
      >
        <el-table-column prop="alarmType" label="类型" width="120" />
        <el-table-column prop="alarmMessage" label="说明" />
        <el-table-column prop="createTime" label="时间" width="180" />
      </el-table>
    </el-card>

    <AiReportPanel v-if="report" :report="report" />
    <el-empty v-else description="选择试验任务后点击「生成报告」" />

    <el-card shadow="never" class="logs-card">
      <template #header>AI 调用日志</template>
      <el-table :data="callLogs" size="small" empty-text="暂无调用记录">
        <el-table-column prop="callTime" label="时间" width="170" />
        <el-table-column prop="analysisType" label="分析类型" width="120" />
        <el-table-column prop="modelName" label="模型" width="140" />
        <el-table-column label="模式" width="80">
          <template #default="{ row }">
            <el-tag :type="row.isMock ? 'info' : 'success'" size="small">
              {{ row.isMock ? 'Mock' : 'API' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="durationMs" label="耗时(ms)" width="100" />
        <el-table-column prop="tokenUsed" label="Token" width="80" />
        <el-table-column prop="errorMessage" label="失败原因" show-overflow-tooltip />
      </el-table>
    </el-card>
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
.summary-card,
.logs-card {
  margin-bottom: 12px;
}
</style>
