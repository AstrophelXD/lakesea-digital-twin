<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { listExperiments } from '@/api/experiment'
import { getExperimentReplay, type ReplayData } from '@/api/experiment'
import { uploadFile, downloadFile } from '@/api/file'
import type { UploadFile } from 'element-plus'
import { ALARM_TYPE_LABELS } from '@/api/alarm'
import TrackReplay from '@/components/TrackReplay.vue'
import { statusLabel, statusTagType } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const experiments = ref<{ id: number; taskNo: string; expName: string; status: string }[]>([])
const selectedId = ref<number | undefined>()
const replay = ref<ReplayData | null>(null)
const loading = ref(false)
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

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

async function loadReplay() {
  if (!selectedId.value) return
  loading.value = true
  try {
    const { data } = await getExperimentReplay(selectedId.value)
    replay.value = data.data!
    renderChart()
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value || !replay.value?.sensorSeries.length) return
  if (!chart) chart = echarts.init(chartRef.value)
  const s = replay.value.sensorSeries
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['速度', '电量', '阻力'] },
    xAxis: {
      type: 'category',
      data: s.map((p) => p.timestamp.slice(11, 19)),
    },
    yAxis: [{ type: 'value' }, { type: 'value', max: 100 }],
    series: [
      { name: '速度', type: 'line', data: s.map((p) => p.speed), smooth: true },
      { name: '电量', type: 'line', yAxisIndex: 1, data: s.map((p) => p.battery), smooth: true },
      { name: '阻力', type: 'line', data: s.map((p) => p.resistance), smooth: true },
    ],
  })
}

async function onUpload(file: File) {
  if (!selectedId.value) return
  await uploadFile(selectedId.value, file, 'REPORT')
  ElMessage.success('上传成功')
  loadReplay()
}

function goAiReport() {
  if (selectedId.value) {
    router.push({ name: 'ai-report', query: { experimentId: String(selectedId.value) } })
  }
}

onMounted(async () => {
  await loadExperiments()
  await loadReplay()
})
</script>

<template>
  <div v-loading="loading">
    <el-card shadow="never" class="toolbar-card">
      <el-select
        v-model="selectedId"
        placeholder="选择已完成的试验"
        style="width: 300px"
        @change="loadReplay"
      >
        <el-option
          v-for="e in experiments"
          :key="e.id"
          :label="`${e.taskNo} - ${e.expName}`"
          :value="e.id"
        />
      </el-select>
      <el-button type="primary" :disabled="!selectedId" @click="goAiReport">AI 分析报告</el-button>
      <el-upload
        v-if="selectedId"
        :auto-upload="false"
        :show-file-list="false"
        @change="(uf: UploadFile) => uf.raw && onUpload(uf.raw)"
      >
        <el-button>上传资料</el-button>
      </el-upload>
    </el-card>

    <template v-if="replay">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card shadow="never">
            <template #header>归档统计</template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="状态">
                <el-tag :type="statusTagType(replay.task.status)">
                  {{ statusLabel(replay.task.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="采样点">{{ replay.stats.pointCount }}</el-descriptions-item>
              <el-descriptions-item label="最大速度">
                {{ replay.stats.maxSpeed?.toFixed(2) ?? '-' }} m/s
              </el-descriptions-item>
              <el-descriptions-item label="最低电量">
                {{ replay.stats.minBattery?.toFixed(1) ?? '-' }}%
              </el-descriptions-item>
              <el-descriptions-item label="告警数">{{ replay.stats.alarmCount }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :span="18">
          <el-card shadow="never">
            <template #header>轨迹回放</template>
            <TrackReplay :tracks="replay.tracks" />
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="section">
        <template #header>历史曲线</template>
        <div ref="chartRef" class="history-chart" />
      </el-card>

      <el-row :gutter="16" class="section">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>告警记录</template>
            <el-table :data="replay.alarms" size="small" max-height="240">
              <el-table-column label="类型" width="110">
                <template #default="{ row }">
                  {{ ALARM_TYPE_LABELS[row.alarmType] || row.alarmType }}
                </template>
              </el-table-column>
              <el-table-column prop="alarmMessage" label="内容" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>试验文件</template>
            <el-table :data="replay.files" size="small" max-height="240">
              <el-table-column prop="fileName" label="文件名" />
              <el-table-column prop="fileType" label="类型" width="90" />
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button link type="primary" @click="downloadFile(row.id, row.fileName)">
                    下载
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<style scoped>
.toolbar-card :deep(.el-card__body) {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
.section {
  margin-top: 16px;
}
.history-chart {
  height: 300px;
}
</style>
