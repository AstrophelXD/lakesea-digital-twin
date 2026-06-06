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
  triggerDemoAlarm,
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
const wsStatus = ref<'connected' | 'reconnecting' | 'disconnected'>('disconnected')
const shipAlarm = ref(false)
const latestFrame = ref<MonitorFrame | null>(null)
const frameHistory = ref<MonitorFrame[]>([])
const tracks = ref<{ x: number; y: number }[]>([])
const recentAlarms = ref<AlarmRecord[]>([])

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
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

const wsStatusLabel = computed(() => {
  const map = { connected: '已连接', reconnecting: '重连中', disconnected: '已断开' }
  return map[wsStatus.value]
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

function scheduleReconnect() {
  if (reconnectTimer) clearTimeout(reconnectTimer)
  wsStatus.value = 'reconnecting'
  reconnectTimer = setTimeout(() => {
    if (selectedId.value && monitorRunning.value) connectWs()
  }, 2000)
}

function connectWs() {
  if (!selectedId.value) return
  disconnectWs(false)
  const token = localStorage.getItem('token')
  if (!token) return
  ws = new WebSocket(buildMonitorWsUrl(selectedId.value, token))
  ws.onopen = () => {
    wsStatus.value = 'connected'
  }
  ws.onclose = () => {
    wsStatus.value = 'disconnected'
    if (monitorRunning.value) scheduleReconnect()
  }
  ws.onerror = () => {
    wsStatus.value = 'disconnected'
  }
  ws.onmessage = (ev) => {
    const frame = JSON.parse(ev.data) as MonitorFrame
    latestFrame.value = frame
    frameHistory.value = [...frameHistory.value, frame].slice(-maxHistory)
    tracks.value = [...tracks.value, { x: frame.position.x, y: frame.position.y }].slice(-200)
    if (frame.alarm) {
      shipAlarm.value = true
      setTimeout(() => { shipAlarm.value = false }, 3000)
      loadAlarms()
      ElMessage.warning(frame.alarm.message)
    }
  }
}

function disconnectWs(resetStatus = true) {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  ws?.close()
  ws = null
  if (resetStatus) wsStatus.value = 'disconnected'
}

async function onStart() {
  if (!selectedId.value) {
    ElMessage.warning('请选择试验任务')
    return
  }
  connectWs()
  await startMonitor(selectedId.value)
  monitorRunning.value = true
  ElMessage.success('模拟试验已启动')
}

async function onStop() {
  if (!selectedId.value) return
  await stopMonitor(selectedId.value)
  monitorRunning.value = false
  disconnectWs()
  ElMessage.info('模拟试验已结束')
}

async function onDemoAlarm(type: string) {
  if (!selectedId.value) return
  await triggerDemoAlarm(selectedId.value, type)
  shipAlarm.value = true
  setTimeout(() => { shipAlarm.value = false }, 3000)
  await loadAlarms()
  ElMessage.warning('演示告警已触发')
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
  if (selectedId.value && monitorRunning.value) connectWs()
})

onUnmounted(() => {
  disconnectWs()
})
</script>

<template>
  <div class="monitor-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-tag :type="wsStatus === 'connected' ? 'success' : wsStatus === 'reconnecting' ? 'warning' : 'info'">
          WebSocket {{ wsStatusLabel }}
        </el-tag>
        <el-tag :type="monitorRunning ? 'success' : 'warning'">
          模拟 {{ monitorRunning ? '运行中' : '已停止' }}
        </el-tag>
        <el-button type="success" :disabled="!selectedId" @click="onStart">模拟试验开始</el-button>
        <el-button :disabled="!selectedId" @click="onStop">暂停 / 结束</el-button>
        <el-divider direction="vertical" />
        <el-button size="small" :disabled="!monitorRunning" @click="onDemoAlarm('LOW_BATTERY')">低电量告警</el-button>
        <el-button size="small" :disabled="!monitorRunning" @click="onDemoAlarm('OUT_OF_BOUNDARY')">越界告警</el-button>
        <el-button size="small" :disabled="!monitorRunning" @click="onDemoAlarm('DATA_SPIKE')">数据突变告警</el-button>
      </div>
    </el-card>

    <el-row :gutter="12" class="main-grid">
      <!-- 左侧：任务与设备 -->
      <el-col :span="5">
        <el-card shadow="never" class="panel">
          <template #header>试验任务与设备</template>
          <el-select
            v-model="selectedId"
            placeholder="选择试验"
            style="width: 100%"
            @change="onExperimentChange"
          >
            <el-option
              v-for="e in experiments"
              :key="e.id"
              :label="`${e.taskNo} - ${e.expName}`"
              :value="e.id"
            />
          </el-select>
          <el-alert
            v-if="!experiments.length"
            title="请先在试验任务页启动试验"
            type="info"
            :closable="false"
            show-icon
            class="side-tip"
          />
          <div v-if="latestFrame" class="device-list">
            <div class="device-item">模型船 {{ latestFrame.shipCode }}</div>
            <div class="device-item">IMU 传感器</div>
            <div class="device-item">阻力传感器</div>
          </div>
        </el-card>
      </el-col>

      <!-- 中间：2.5D 场景 -->
      <el-col :span="11">
        <el-card shadow="never" class="panel scene-panel">
          <template #header>水池 / 湖海试验场 2.5D 场景</template>
          <TwinScene
            :position="position"
            :heading="heading"
            :tracks="tracks"
            :highlight="shipAlarm"
          />
        </el-card>
      </el-col>

      <!-- 右侧：实时数据 -->
      <el-col :span="8">
        <el-card shadow="never" class="panel">
          <template #header>实时数据面板</template>
          <el-row :gutter="8">
            <el-col v-for="m in metrics" :key="m.label" :span="12">
              <div class="metric-box">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value">{{ m.value }}</div>
              </div>
            </el-col>
          </el-row>
          <div class="alarm-section">
            <div class="alarm-title">实时告警</div>
            <AlarmList :alarms="recentAlarms" compact />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部：曲线 -->
    <el-card shadow="never" class="chart-card">
      <template #header>速度 / 姿态 / 阻力 / 电量曲线</template>
      <SensorChart :frames="frameHistory" />
    </el-card>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.main-grid {
  margin-top: 12px;
}
.panel {
  min-height: 420px;
}
.scene-panel :deep(.el-card__body) {
  padding: 8px;
}
.side-tip {
  margin-top: 12px;
}
.device-list {
  margin-top: 16px;
}
.device-item {
  padding: 8px 10px;
  background: #f3f4f6;
  border-radius: 6px;
  margin-bottom: 6px;
  font-size: 13px;
}
.metric-box {
  background: #f3f4f6;
  border-radius: 8px;
  padding: 10px;
  text-align: center;
  margin-bottom: 8px;
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
.alarm-section {
  margin-top: 12px;
}
.alarm-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}
.chart-card {
  margin-top: 12px;
}
</style>
