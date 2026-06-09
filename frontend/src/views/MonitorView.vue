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
import type { DeviceInfo, DeviceStatusEvent } from '@/api/device'
import SensorChart from '@/components/SensorChart.vue'
import MonitorStatusBar from '@/components/monitor/MonitorStatusBar.vue'
import DeviceControlPanel from '@/components/monitor/DeviceControlPanel.vue'
import VideoTwinPanel from '@/components/monitor/VideoTwinPanel.vue'
import RealtimeStatusPanel from '@/components/monitor/RealtimeStatusPanel.vue'
import '@/components/monitor/monitor-theme.css'

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
const controlPanelRef = ref<InstanceType<typeof DeviceControlPanel> | null>(null)
const deviceList = ref<DeviceInfo[]>([])

const isMqttMode = computed(() => mqttInfo.value?.enabled === true)
const dataSourceLabel = computed(() =>
  isMqttMode.value ? 'MQTT 接入' : 'WebSocket 模拟',
)

const selectedExperiment = computed(() =>
  experiments.value.find((e) => e.id === selectedId.value) ?? null,
)

const onlineDeviceCount = computed(() => deviceList.value.filter((d) => d.online).length)
const totalDeviceCount = computed(() => deviceList.value.length || 6)

const position = computed(() => {
  if (useCvPosition.value && cvTrack.value) {
    return { x: cvTrack.value.poolX, y: cvTrack.value.poolY }
  }
  return latestFrame.value?.position ?? { x: 10, y: 10 }
})

const heading = computed(() => latestFrame.value?.heading ?? 0)
const speed = computed(() => latestFrame.value?.speed ?? null)
const battery = computed(() => latestFrame.value?.battery ?? null)

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let healthTimer: ReturnType<typeof setInterval> | null = null
const maxHistory = 60

function calcLatency(frame: MonitorFrame) {
  const ts = frame.serverTime || frame.timestamp
  const serverMs = Date.parse(ts.replace(' ', 'T'))
  if (!Number.isNaN(serverMs)) {
    wsLatencyMs.value = Math.max(0, Date.now() - serverMs)
  }
}

function onDevicesLoaded(devices: DeviceInfo[]) {
  deviceList.value = devices
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
  <div class="monitor-console">
    <!-- 顶栏：标题 + 状态 -->
    <div class="top-area">
      <div class="page-header">
        <h1 class="page-title">湖海试验场 · 智能中控台</h1>
        <span class="page-sub">数字孪生 / 视频感知 / 设备控制</span>
      </div>
      <MonitorStatusBar
        :ws-status="wsStatus"
        :monitor-running="monitorRunning"
        :health="systemHealth"
        :ws-latency-ms="wsLatencyMs"
        :data-source-label="dataSourceLabel"
        :experiment="selectedExperiment"
      />
    </div>

    <!-- 操作条 -->
    <div class="console-card action-bar">
      <el-select
        v-model="selectedId"
        placeholder="选择试验任务"
        size="default"
        class="exp-select"
        @change="onExperimentChange"
      >
        <el-option
          v-for="e in experiments"
          :key="e.id"
          :label="`${e.taskNo} - ${e.expName}`"
          :value="e.id"
        />
      </el-select>
      <el-button type="primary" :disabled="!selectedId" @click="onStart">
        {{ isMqttMode ? '开始监控' : '▶ 启动' }}
      </el-button>
      <el-button :disabled="!selectedId" @click="onStop">⏹ 暂停</el-button>
      <el-switch
        v-model="useCvPosition"
        inline-prompt
        active-text="CV"
        inactive-text="传感器"
        size="small"
      />
      <div class="action-divider" />
      <el-button size="small" plain :disabled="!monitorRunning" @click="onDemoAlarm('LOW_BATTERY')">低电量</el-button>
      <el-button size="small" plain :disabled="!monitorRunning" @click="onDemoAlarm('OUT_OF_BOUNDARY')">越界</el-button>
      <el-button size="small" plain :disabled="!monitorRunning" @click="onDemoAlarm('DATA_SPIKE')">突变</el-button>
    </div>

    <!-- 两栏主体：左视觉屏 / 右侧栏 -->
    <div class="console-body">
      <!-- 左：视频 + 孪生 + 曲线 -->
      <div class="col-visual">
        <div class="console-card visual-card">
          <div class="console-card-header">
            <span><i class="dot" />视频感知 + 数字孪生</span>
          </div>
          <div class="console-card-body visual-body">
            <VideoTwinPanel
              :experiment-id="selectedId"
              :cv-track="cvTrack"
              :running="monitorRunning"
              :position="position"
              :heading="heading"
              :tracks="tracks"
              :highlight="shipAlarm"
              :speed="speed ?? undefined"
              :battery="battery ?? undefined"
            />
          </div>
        </div>

        <div class="console-card chart-card">
          <div class="console-card-header">
            <span><i class="dot" />实时曲线</span>
            <span class="chart-hint">{{ frameHistory.length }} 点</span>
          </div>
          <div class="console-card-body chart-body">
            <SensorChart :frames="frameHistory" />
          </div>
        </div>
      </div>

      <!-- 右：指标 + 控制 -->
      <aside class="col-side">
        <div class="console-card side-card">
          <div class="console-card-header">
            <span><i class="dot" />运行指标与告警</span>
          </div>
          <div class="console-card-body">
            <RealtimeStatusPanel
              :latest-frame="latestFrame"
              :alarms="recentAlarms"
              :health="systemHealth"
              :online-device-count="onlineDeviceCount"
              :total-device-count="totalDeviceCount"
              :monitor-running="monitorRunning"
              compact
            />
          </div>
        </div>

        <div class="console-card side-card">
          <div class="console-card-header">
            <span><i class="dot" />设备控制台</span>
          </div>
          <div class="console-card-body">
            <el-alert
              v-if="!experiments.length"
              title="请先在试验任务页启动试验"
              type="info"
              :closable="false"
              show-icon
              class="side-tip"
            />
            <DeviceControlPanel
              ref="controlPanelRef"
              :experiment-id="selectedId"
              :monitor-running="monitorRunning"
              :mqtt-enabled="isMqttMode"
              :battery="battery"
              compact
              @command-issued="loadSystemHealth"
              @devices-loaded="onDevicesLoaded"
            />
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.monitor-console {
  min-height: 100%;
  padding-bottom: 12px;
}
.top-area {
  margin-bottom: 10px;
}
.page-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}
.page-title {
  font-size: 17px;
  font-weight: 700;
  color: #0f766e;
  margin: 0;
}
.page-sub {
  font-size: 12px;
  color: #94a3b8;
}
.top-area :deep(.status-bar) {
  margin-bottom: 0;
}

.action-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 10px;
}
.exp-select {
  width: 240px;
}
.action-divider {
  width: 1px;
  height: 20px;
  background: #e2e8f0;
  margin: 0 4px;
}

/* 两栏布局：左宽右窄，始终并排（内容区约 900px+ 即可） */
.console-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 10px;
  align-items: start;
}

.col-visual {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.col-side {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.visual-body {
  padding: 8px !important;
}

.chart-body {
  padding: 4px 10px 10px !important;
}

.chart-hint {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 400;
}

.side-tip {
  margin-bottom: 8px;
}

/* 极窄屏才单列，且视觉屏在上 */
@media (max-width: 860px) {
  .console-body {
    grid-template-columns: 1fr;
  }
}
</style>
