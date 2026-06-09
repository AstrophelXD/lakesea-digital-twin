<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  exportAiReport,
  exportSensorCsv,
  exportTrackJson,
  getExperimentReplay,
  listExperiments,
  type ExperimentTask,
  type ReplayData,
} from '@/api/experiment'
import { uploadFile } from '@/api/file'
import { downloadFile } from '@/api/file'
import type { UploadFile } from 'element-plus'
import { ALARM_TYPE_LABELS } from '@/api/alarm'
import TrackReplay from '@/components/TrackReplay.vue'
import { statusLabel, statusTagType } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const experiments = ref<ExperimentTask[]>([])
const selectedId = ref<number | undefined>()
const replay = ref<ReplayData | null>(null)
const loading = ref(false)
const replayIndex = ref(0)
const playing = ref(false)
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let playTimer: ReturnType<typeof setInterval> | null = null

const FILE_TYPES = [
  { value: 'REPORT', label: '试验报告' },
  { value: 'RAW_DATA', label: '原始数据' },
  { value: 'VIDEO', label: '视频占位' },
]
const uploadType = ref('REPORT')

const maxIndex = computed(() =>
  Math.max((replay.value?.sensorSeries?.length || 1) - 1, 0),
)

const replayTracks = computed(() => {
  const tracks = replay.value?.tracks || []
  if (!tracks.length) return []
  const ratio = maxIndex.value > 0 ? replayIndex.value / maxIndex.value : 1
  const end = Math.min(
    tracks.length - 1,
    Math.max(0, Math.round(ratio * (tracks.length - 1))),
  )
  return tracks.slice(0, end + 1)
})

const currentSensor = computed(() => replay.value?.sensorSeries?.[replayIndex.value] || null)

const currentAlarms = computed(() => {
  if (!replay.value) return []
  return replay.value.alarmMarkers.filter((m) => m.seriesIndex === replayIndex.value)
})

const sliderMarks = computed(() => {
  const marks: Record<number, string> = {}
  replay.value?.alarmMarkers.forEach((m) => {
    marks[m.seriesIndex] = '⚠'
  })
  return marks
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

function selectExperiment(row: ExperimentTask) {
  selectedId.value = row.id
  loadReplay()
}

async function loadReplay() {
  if (!selectedId.value) return
  stopPlay()
  loading.value = true
  try {
    const { data } = await getExperimentReplay(selectedId.value)
    replay.value = data.data!
    replayIndex.value = 0
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
    legend: { data: ['速度', '电量', '阻力', '横摇'] },
    xAxis: { type: 'category', data: s.map((p) => p.timestamp.slice(11, 19)) },
    yAxis: [{ type: 'value', name: 'm/s / N / deg' }, { type: 'value', max: 100, name: '%' }],
    series: [
      { name: '速度', type: 'line', data: s.map((p) => p.speed), smooth: true },
      { name: '电量', type: 'line', yAxisIndex: 1, data: s.map((p) => p.battery), smooth: true },
      { name: '阻力', type: 'line', data: s.map((p) => p.resistance), smooth: true },
      { name: '横摇', type: 'line', data: s.map((p) => p.roll), smooth: true },
    ],
  })
  highlightChartIndex(replayIndex.value)
}

function highlightChartIndex(idx: number) {
  if (!chart || !replay.value?.sensorSeries.length) return
  chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: idx })
}

function stopPlay() {
  playing.value = false
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

function togglePlay() {
  if (playing.value) {
    stopPlay()
    return
  }
  if (!replay.value?.sensorSeries.length) return
  playing.value = true
  playTimer = setInterval(() => {
    if (replayIndex.value >= maxIndex.value) {
      stopPlay()
      return
    }
    replayIndex.value += 1
  }, 400)
}

watch(replayIndex, (idx) => highlightChartIndex(idx))

async function onUpload(file: File) {
  if (!selectedId.value) return
  await uploadFile(selectedId.value, file, uploadType.value)
  ElMessage.success('文件已上传')
  loadReplay()
}

function goAiReport() {
  if (selectedId.value) {
    router.push({ name: 'ai-report', query: { experimentId: String(selectedId.value) } })
  }
}

async function handleExport(fn: () => Promise<void>, label: string) {
  if (!selectedId.value) return
  try {
    await fn()
    ElMessage.success(`${label} 已导出`)
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : `${label} 导出失败`)
  }
}

function handleResize() {
  chart?.resize()
}

onMounted(async () => {
  await loadExperiments()
  await loadReplay()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopPlay()
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<template>
  <div v-loading="loading" class="archive-page">
    <el-row :gutter="16">
      <!-- 历史试验列表 -->
      <el-col :span="7">
        <el-card shadow="never" class="list-card">
          <template #header>历史试验列表</template>
          <el-table
            :data="experiments"
            size="small"
            highlight-current-row
            :current-row-key="selectedId"
            row-key="id"
            max-height="520"
            @row-click="selectExperiment"
          >
            <el-table-column prop="taskNo" label="任务单号" width="130" />
            <el-table-column prop="expName" label="试验名称" show-overflow-tooltip />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!experiments.length" description="暂无已完成/已归档试验" />
        </el-card>
      </el-col>

      <!-- 回放主区 -->
      <el-col :span="17">
        <el-card v-if="replay" shadow="never">
          <template #header>
            <div class="replay-header">
              <span>{{ replay.task.taskNo }} — {{ replay.task.expName }}</span>
              <el-tag :type="statusTagType(replay.task.status)" size="small">
                {{ statusLabel(replay.task.status) }}
              </el-tag>
            </div>
          </template>

          <div class="toolbar">
            <el-button type="primary" @click="goAiReport">AI 分析报告</el-button>
            <el-dropdown>
              <el-button>导出数据</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    @click="handleExport(() => exportSensorCsv(selectedId!), '传感器 CSV')"
                  >
                    传感器 CSV
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="handleExport(() => exportTrackJson(selectedId!), '轨迹 JSON')"
                  >
                    轨迹 JSON
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="handleExport(() => exportAiReport(selectedId!, 'markdown'), 'AI 报告 Markdown')"
                  >
                    AI 报告 Markdown
                  </el-dropdown-item>
                  <el-dropdown-item
                    @click="handleExport(() => exportAiReport(selectedId!, 'html'), 'AI 报告 HTML')"
                  >
                    AI 报告 HTML
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-select v-model="uploadType" style="width: 120px" size="default">
              <el-option
                v-for="t in FILE_TYPES"
                :key="t.value"
                :label="t.label"
                :value="t.value"
              />
            </el-select>
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              @change="(uf: UploadFile) => uf.raw && onUpload(uf.raw)"
            >
              <el-button>上传文件</el-button>
            </el-upload>
          </div>

          <el-row :gutter="12" class="stats-row">
            <el-col :span="4">
              <div class="stat-box">
                <div class="stat-num">{{ replay.stats.pointCount }}</div>
                <div class="stat-lbl">采样点</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="stat-box">
                <div class="stat-num">{{ replay.stats.maxSpeed?.toFixed(1) ?? '-' }}</div>
                <div class="stat-lbl">最大速度 m/s</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="stat-box">
                <div class="stat-num">{{ replay.stats.minBattery?.toFixed(0) ?? '-' }}%</div>
                <div class="stat-lbl">最低电量</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="stat-box">
                <div class="stat-num">{{ replay.stats.alarmCount }}</div>
                <div class="stat-lbl">告警数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div v-if="replay.aiReport" class="ai-brief">
                <el-tag type="success" size="small">已生成 AI 报告</el-tag>
                <span class="ai-title">{{ replay.aiReport.reportTitle }}</span>
              </div>
              <el-tag v-else type="info" size="small">尚未生成 AI 报告</el-tag>
            </el-col>
          </el-row>

          <!-- 轨迹回放 -->
          <TrackReplay
            :tracks="replayTracks"
            :index="replayIndex"
            controlled
            :highlight="currentAlarms.length > 0"
            @update:index="(v) => (replayIndex = v)"
          />

          <!-- 统一时间轴 -->
          <div class="timeline-bar">
            <el-button size="small" :type="playing ? 'warning' : 'primary'" @click="togglePlay">
              {{ playing ? '暂停' : '播放' }}
            </el-button>
            <el-button size="small" @click="replayIndex = 0; stopPlay()">重置</el-button>
            <span class="replay-time">{{ currentSensor?.timestamp?.slice(11, 19) || '—' }}</span>
            <el-slider
              v-model="replayIndex"
              class="timeline-slider"
              :min="0"
              :max="maxIndex"
              :marks="sliderMarks"
              :format-tooltip="(v: number) => replay?.sensorSeries?.[v]?.timestamp?.slice(11, 19) || ''"
              @change="stopPlay"
            />
          </div>

          <el-descriptions v-if="currentSensor" :column="4" border size="small" class="sensor-now">
            <el-descriptions-item label="速度">{{ currentSensor.speed ?? '-' }} m/s</el-descriptions-item>
            <el-descriptions-item label="电量">{{ currentSensor.battery ?? '-' }}%</el-descriptions-item>
            <el-descriptions-item label="阻力">{{ currentSensor.resistance ?? '-' }} N</el-descriptions-item>
            <el-descriptions-item label="横摇">{{ currentSensor.roll ?? '-' }}°</el-descriptions-item>
          </el-descriptions>

          <el-alert
            v-for="a in currentAlarms"
            :key="a.alarmId"
            :title="ALARM_TYPE_LABELS[a.alarmType] || a.alarmType"
            :description="a.alarmMessage"
            type="warning"
            show-icon
            :closable="false"
            class="alarm-alert"
          />
        </el-card>
        <el-empty v-else description="请选择左侧历史试验" />
      </el-col>
    </el-row>

    <template v-if="replay">
      <el-card shadow="never" class="section">
        <template #header>历史曲线（随时间轴同步）</template>
        <div ref="chartRef" class="history-chart" />
      </el-card>

      <el-row :gutter="16" class="section">
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>告警记录（时间轴 ⚠ 标记）</template>
            <el-table :data="replay.alarms" size="small" max-height="260">
              <el-table-column label="时间" width="90">
                <template #default="{ row }">{{ row.createTime?.slice(11, 19) }}</template>
              </el-table-column>
              <el-table-column label="类型" width="120">
                <template #default="{ row }">
                  {{ ALARM_TYPE_LABELS[row.alarmType] || row.alarmType }}
                </template>
              </el-table-column>
              <el-table-column prop="alarmMessage" label="内容" />
              <el-table-column label="定位" width="70">
                <template #default="{ row }">
                  <el-button
                    link
                    type="primary"
                    @click="replayIndex = replay.alarmMarkers.find((m) => m.alarmId === row.id)?.seriesIndex ?? 0"
                  >
                    跳转
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="never">
            <template #header>试验文件</template>
            <el-table :data="replay.files" size="small" max-height="260">
              <el-table-column prop="fileName" label="文件名" />
              <el-table-column label="类型" width="100">
                <template #default="{ row }">
                  {{ FILE_TYPES.find((t) => t.value === row.fileType)?.label || row.fileType }}
                </template>
              </el-table-column>
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
.archive-page {
  min-height: 400px;
}
.list-card {
  height: 100%;
}
.replay-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.stats-row {
  margin-bottom: 12px;
}
.stat-box {
  background: #f3f4f6;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}
.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: #0f766e;
}
.stat-lbl {
  font-size: 12px;
  color: #6b7280;
}
.ai-brief {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 100%;
}
.ai-title {
  font-size: 13px;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.timeline-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}
.timeline-slider {
  flex: 1;
}
.replay-time {
  font-size: 13px;
  color: #0f766e;
  font-weight: 600;
  min-width: 64px;
}
.sensor-now {
  margin-top: 10px;
}
.alarm-alert {
  margin-top: 8px;
}
.section {
  margin-top: 16px;
}
.history-chart {
  height: 320px;
}
</style>
