<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listExperiments, type ExperimentTask } from '@/api/experiment'
import {
  buildMonitorWsUrl,
  getMonitorStatus,
  startMonitor,
  stopMonitor,
  type MonitorFrame,
} from '@/api/monitor'
import { listAlarms, type AlarmRecord } from '@/api/alarm'
import TwinScene from '@/components/TwinScene.vue'
import SensorChart from '@/components/SensorChart.vue'
import AlarmList from '@/components/AlarmList.vue'

const route = useRoute()
const experiments = ref<ExperimentTask[]>([])
const selectedId = ref<number | undefined>()
const monitorRunning = ref(false)
const wsConnected = ref(false)
const latestFrame = ref<MonitorFrame | null>(null)
const frameHistory = ref<MonitorFrame[]>([])
const tracks = ref<{ x: number; y: number }[]>([])
const recentAlarms = ref<AlarmRecord[]>([])

let ws: WebSocket | null = null
const maxHistory = 60

const position = computed(() => latestFrame.value?.position ?? { x: 10, y: 10 })
const heading = computed(() => latestFrame.value?.heading ?? 0)
const metrics = computed(() => {
  const f = latestFrame.value
  if (!f) return []
  return [
    { label: '速度', value: `${f.speed} m/s` },
    { label: '航向', value: `${f.heading}°` },
    { label: '横摇', value: `${f.roll}°` },
    { label: '纵摇', value: `${f.pitch}°` },
    { label: '电量', value: `${f.battery}%` },
    { label: '阻力', value: `${f.resistance} N` },
  ]
})

async function loadExperiments() {
  const [running, ready] = await Promise.all([
    listExperiments({ status: 'RUNNING', pageSize: 50 }),
    listExperiments({ status: 'READY', pageSize: 50 }),
  ])
  experiments.value = [...running.data.data!.items, ...ready.data.data!.items]
  const qid = route.query.experimentId
  if (qid) selectedId.value = Number(qid)
  else if (!selectedId.value && experiments.value.length) {
    selectedId.value = experiments.value[0].id
  }
}

async function refreshStatus() {
  if (!selectedId.value) return
  const { data } = await getMonitorStatus(selectedId.value)
  monitorRunning.value = data.data!.running
}

function connectWs() {
  if (!selectedId.value) return
  disconnectWs()
  const token = localStorage.getItem('token')
  if (!token) return
  ws = new WebSocket(buildMonitorWsUrl(selectedId.value, token))
  ws.onopen = () => {
    wsConnected.value = true
  }
  ws.onclose = () => {
    wsConnected.value = false
  }
  ws.onmessage = (ev) => {
    const frame = JSON.parse(ev.data) as MonitorFrame
    latestFrame.value = frame
    frameHistory.value = [...frameHistory.value, frame].slice(-maxHistory)
    tracks.value = [...tracks.value, { x: frame.position.x, y: frame.position.y }].slice(-200)
    if (frame.alarm) {
      loadAlarms()
      ElMessage.warning(frame.alarm.message)
    }
  }
}

function disconnectWs() {
  ws?.close()
  ws = null
  wsConnected.value = false
}

async function onStart() {
  if (!selectedId.value) {
    ElMessage.warning('请选择试验任务')
    return
  }
  connectWs()
  await startMonitor(selectedId.value)
  monitorRunning.value = true
  ElMessage.success('模拟数据已启动')
}

async function onStop() {
  if (!selectedId.value) return
  await stopMonitor(selectedId.value)
  monitorRunning.value = false
  ElMessage.info('模拟数据已停止')
}

async function loadAlarms() {
  if (!selectedId.value) return
  const { data } = await listAlarms({ experimentId: selectedId.value, pageSize: 10 })
  recentAlarms.value = data.data!.items
}

function onExperimentChange() {
  latestFrame.value = null
  frameHistory.value = []
  tracks.value = []
  disconnectWs()
  refreshStatus()
  loadAlarms()
}

onMounted(async () => {
  await loadExperiments()
  await refreshStatus()
  await loadAlarms()
  if (selectedId.value) connectWs()
})

onUnmounted(() => {
  disconnectWs()
})
</script>

<template>
  <div class="monitor-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-select
          v-model="selectedId"
          placeholder="选择执行中的试验"
          style="width: 280px"
          @change="onExperimentChange"
        >
          <el-option
            v-for="e in experiments"
            :key="e.id"
            :label="`${e.taskNo} - ${e.expName} (${e.status})`"
            :value="e.id"
          />
        </el-select>
        <el-tag :type="wsConnected ? 'success' : 'info'">
          WebSocket {{ wsConnected ? '已连接' : '未连接' }}
        </el-tag>
        <el-tag :type="monitorRunning ? 'success' : 'warning'">
          模拟 {{ monitorRunning ? '运行中' : '已停止' }}
        </el-tag>
        <el-button type="success" :disabled="!selectedId" @click="onStart">启动模拟</el-button>
        <el-button :disabled="!selectedId" @click="onStop">停止模拟</el-button>
        <el-button @click="loadAlarms">刷新告警</el-button>
      </div>
      <el-alert
        v-if="!experiments.length"
        title="请先在「试验任务」中将任务流转为「已准备」并「启动试验」"
        type="info"
        :closable="false"
        show-icon
        class="tip"
      />
    </el-card>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>数字孪生场景（俯视图）</template>
          <TwinScene :position="position" :heading="heading" :tracks="tracks" />
          <el-row :gutter="12" class="metrics">
            <el-col v-for="m in metrics" :key="m.label" :span="4">
              <div class="metric-box">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value">{{ m.value }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
        <el-card shadow="never" class="chart-card">
          <template #header>实时曲线</template>
          <SensorChart :frames="frameHistory" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>实时告警</template>
          <AlarmList :alarms="recentAlarms" compact />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.tip {
  margin-top: 12px;
}
.chart-card {
  margin-top: 16px;
}
.metrics {
  margin-top: 12px;
}
.metric-box {
  background: #f3f4f6;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}
.metric-label {
  font-size: 12px;
  color: #6b7280;
}
.metric-value {
  font-size: 16px;
  font-weight: 600;
  color: #0f766e;
}
</style>
