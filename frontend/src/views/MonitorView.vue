<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listExperiments, type ExperimentTask } from '@/api/experiment'
import {
  buildMonitorWsUrl,
  getMonitorStatus,
  getMqttInfo,
  startMonitor,
  stopMonitor,
  triggerDemoAlarm,
  type MonitorFrame,
  type MqttInfo,
} from '@/api/monitor'
import { listAlarms, type AlarmRecord } from '@/api/alarm'
import { getSystemHealth, type SystemHealthStatus } from '@/api/health'
import { startCvTracking, stopCvTracking, type CvTrackResult } from '@/api/cv'
import { startVideoRecording, stopVideoRecording } from '@/api/video'
import TwinScene from '@/components/TwinScene.vue'
import SensorChart from '@/components/SensorChart.vue'
import AlarmList from '@/components/AlarmList.vue'
import VideoPanel from '@/components/VideoPanel.vue'
import ControlPanel from '@/components/ControlPanel.vue'
import type { DeviceStatusEvent } from '@/api/device'
import SystemStatusBar from '@/components/SystemStatusBar.vue'

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
const mqttInfo = ref<MqttInfo | null>(null)
const systemHealth = ref<SystemHealthStatus | null>(null)
const cvTrack = ref<CvTrackResult | null>(null)
const cvEnabled = ref(false)
const wsLatencyMs = ref<number | null>(null)
const useCvPosition = ref(true)
const controlPanelRef = ref<InstanceType<typeof ControlPanel> | null>(null)

const isMqttMode = computed(() => mqttInfo.value?.enabled === true)
const dataSourceLabel = computed(() =>
  isMqttMode.value ? 'MQTT 接入' : 'WebSocket 内置模拟',
)

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let healthTimer: ReturnType<typeof setInterval> | null = null
const maxHistory = 60

const position = computed(() => {
  if (useCvPosition.value && cvTrack.value) {
    return { x: cvTrack.value.poolX, y: cvTrack.value.poolY }
  }
  return latestFrame.value?.position ?? { x: 10, y: 10 }
})

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

function calcLatency(frame: MonitorFrame) {
  const ts = frame.serverTime || frame.timestamp
  const serverMs = Date.parse(ts.replace(' ', 'T'))
  if (!Number.isNaN(serverMs)) {
    wsLatencyMs.value = Math.max(0, Date.now() - serverMs)
  }
}

async function loadMqttInfo() {
  const { data } = await getMqttInfo()
  mqttInfo.value = data.data!
}

async function loadSystemHealth() {
  const { data } = await getSystemHealth(selectedId.value)
  systemHealth.value = data.data!
}

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
    const payload = JSON.parse(ev.data)
    if (payload.type === 'cv_track') {
      cvTrack.value = payload as CvTrackResult
      if (useCvPosition.value) {
        tracks.value = [...tracks.value, { x: payload.poolX, y: payload.poolY }].slice(-200)
      }
      return
    }
    if (payload.type === 'device_status') {
      controlPanelRef.value?.applyDeviceStatus(payload as DeviceStatusEvent)
      return
    }
    const frame = payload as MonitorFrame
    latestFrame.value = frame
    calcLatency(frame)
    frameHistory.value = [...frameHistory.value, frame].slice(-maxHistory)
    if (!useCvPosition.value || !cvEnabled.value) {
      tracks.value = [...tracks.value, { x: frame.position.x, y: frame.position.y }].slice(-200)
    }
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
  await startVideoRecording(selectedId.value)
  await startCvTracking(selectedId.value)
  cvEnabled.value = true
  monitorRunning.value = true
  ElMessage.success(isMqttMode.value ? '中控台已启动，请运行 MQTT 发布器' : '智能中控台已启动')
}

async function onStop() {
  if (!selectedId.value) return
  await stopMonitor(selectedId.value)
  await stopVideoRecording(selectedId.value).catch(() => {})
  await stopCvTracking(selectedId.value)
  cvEnabled.value = false
  monitorRunning.value = false
  disconnectWs()
  ElMessage.info('监控已暂停')
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
  cvTrack.value = null
  disconnectWs()
  refreshStatus()
  loadAlarms()
  loadSystemHealth()
}

onMounted(async () => {
  await Promise.all([loadExperiments(), loadMqttInfo()])
  await refreshStatus()
  await loadAlarms()
  await loadSystemHealth()
  healthTimer = setInterval(loadSystemHealth, 5000)
  if (selectedId.value && monitorRunning.value) connectWs()
})

onUnmounted(() => {
  disconnectWs()
  if (healthTimer) clearInterval(healthTimer)
})
</script>

<template>
  <div class="monitor-page">
    <div class="page-title">数字孪生监控 · 智能中控台</div>

    <SystemStatusBar
      :ws-status="wsStatus"
      :monitor-running="monitorRunning"
      :health="systemHealth"
      :ws-latency-ms="wsLatencyMs"
      :mqtt-latency-ms="null"
      :data-source-label="dataSourceLabel"
    />

    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <el-select
          v-model="selectedId"
          placeholder="选择试验任务"
          style="width: 280px"
          @change="onExperimentChange"
        >
          <el-option
            v-for="e in experiments"
            :key="e.id"
            :label="`${e.taskNo} - ${e.expName}`"
            :value="e.id"
          />
        </el-select>
        <el-button type="success" :disabled="!selectedId" @click="onStart">
          {{ isMqttMode ? '开始监控' : '启动中控台' }}
        </el-button>
        <el-button :disabled="!selectedId" @click="onStop">暂停 / 结束</el-button>
        <el-switch
          v-model="useCvPosition"
          active-text="CV 驱动孪生"
          inactive-text="传感器驱动"
          style="margin-left: 8px"
        />
        <el-divider direction="vertical" />
        <el-button size="small" :disabled="!monitorRunning" @click="onDemoAlarm('LOW_BATTERY')">低电量</el-button>
        <el-button size="small" :disabled="!monitorRunning" @click="onDemoAlarm('OUT_OF_BOUNDARY')">越界</el-button>
        <el-button size="small" :disabled="!monitorRunning" @click="onDemoAlarm('DATA_SPIKE')">数据突变</el-button>
      </div>
    </el-card>

    <el-row :gutter="12" class="main-grid">
      <el-col :span="5">
        <el-card shadow="never" class="panel">
          <template #header>试验任务与设备控制</template>
          <el-alert
            v-if="!experiments.length"
            title="请先在试验任务页启动试验"
            type="info"
            :closable="false"
            show-icon
            class="side-tip"
          />
          <ControlPanel
            ref="controlPanelRef"
            :experiment-id="selectedId"
            :monitor-running="monitorRunning"
            :mqtt-enabled="isMqttMode"
            @command-issued="loadSystemHealth"
          />
        </el-card>
      </el-col>

      <el-col :span="11">
        <el-card shadow="never" class="panel center-panel">
          <template #header>视频感知 + 数字孪生联动</template>
          <VideoPanel
            :experiment-id="selectedId"
            :cv-track="cvTrack"
            :running="monitorRunning"
          />
          <div class="twin-section">
            <div class="section-label">数字孪生水池场景</div>
            <TwinScene
              :position="position"
              :heading="heading"
              :tracks="tracks"
              :highlight="shipAlarm"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="panel">
          <template #header>实时数据 · 告警 · 系统状态</template>
          <el-row :gutter="8">
            <el-col v-for="m in metrics" :key="m.label" :span="12">
              <div class="metric-box">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value">{{ m.value }}</div>
              </div>
            </el-col>
          </el-row>
          <div v-if="systemHealth" class="health-cards">
            <div class="health-item">
              <span>后端服务</span>
              <el-tag size="small" :type="systemHealth.backend === 'UP' ? 'success' : 'danger'">
                {{ systemHealth.backend === 'UP' ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="health-item">
              <span>数据库</span>
              <el-tag size="small" :type="systemHealth.database === 'UP' ? 'success' : 'danger'">
                {{ systemHealth.database === 'UP' ? '正常' : '异常' }}
              </el-tag>
            </div>
            <div class="health-item">
              <span>MQTT Broker</span>
              <el-tag size="small" :type="systemHealth.mqttBroker === 'UP' ? 'success' : 'info'">
                {{ systemHealth.mqttBroker }}
              </el-tag>
            </div>
            <div class="health-item">
              <span>视频流</span>
              <el-tag size="small" type="success">{{ systemHealth.videoStream }}</el-tag>
            </div>
            <div class="health-item">
              <span>边缘端</span>
              <el-tag size="small" :type="systemHealth.edgeAgent === 'UP' ? 'success' : 'warning'">
                {{ systemHealth.edgeAgent }}
              </el-tag>
            </div>
          </div>
          <div class="alarm-section">
            <div class="alarm-title">实时告警</div>
            <AlarmList :alarms="recentAlarms" compact />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="chart-card">
      <template #header>速度 / 姿态 / 阻力 / 电量曲线 · 轨迹回放</template>
      <SensorChart :frames="frameHistory" />
    </el-card>
  </div>
</template>

<style scoped>
.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f766e;
  margin-bottom: 12px;
}
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
  min-height: 520px;
}
.center-panel :deep(.el-card__body) {
  padding: 10px;
}
.twin-section {
  margin-top: 10px;
}
.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 6px;
}
.side-tip {
  margin-bottom: 12px;
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
.health-cards {
  margin: 12px 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  padding: 6px 8px;
  background: #f8fafc;
  border-radius: 6px;
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
