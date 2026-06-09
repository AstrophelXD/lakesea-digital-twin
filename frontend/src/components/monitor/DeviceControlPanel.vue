<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  emergencyStopDevice,
  issueDeviceCommand,
  listDeviceCommands,
  listDevices,
  type DeviceCommand,
  type DeviceInfo,
  type DeviceStatusEvent,
} from '@/api/device'

const props = defineProps<{
  experimentId?: number
  monitorRunning?: boolean
  mqttEnabled?: boolean
  battery?: number | null
  compact?: boolean
}>()

const emit = defineEmits<{
  commandIssued: []
  devicesLoaded: [devices: DeviceInfo[]]
}>()

const devices = ref<DeviceInfo[]>([])
const selectedDevice = ref('')
const speedValue = ref(1.5)
const headingValue = ref(45)
const loading = ref(false)
const recentCommands = ref<DeviceCommand[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

async function loadDevices() {
  const { data } = await listDevices(props.experimentId)
  devices.value = data.data ?? []
  if (!selectedDevice.value && devices.value.length) {
    selectedDevice.value = devices.value[0].deviceId
  }
  emit('devicesLoaded', devices.value)
}

async function loadRecentCommands() {
  if (!selectedDevice.value) return
  const { data } = await listDeviceCommands(selectedDevice.value, props.experimentId)
  recentCommands.value = (data.data?.items ?? []).slice(0, 4)
}

function selectDevice(id: string) {
  selectedDevice.value = id
  loadRecentCommands()
}

function applyDeviceStatus(event: DeviceStatusEvent) {
  const idx = devices.value.findIndex((d) => d.deviceId === event.deviceId)
  if (idx < 0) return
  const d = devices.value[idx]
  devices.value[idx] = {
    ...d,
    status: event.status || d.status,
    online: true,
    lastCommandType: event.commandType ?? d.lastCommandType,
    lastAckAt: event.executedAt ?? event.receivedAt ?? d.lastAckAt,
    ackStatus: event.status ?? d.ackStatus,
  }
  if (selectedDevice.value === event.deviceId) loadRecentCommands()
  emit('devicesLoaded', devices.value)
}

async function sendCommand(commandType: string, payload?: Record<string, unknown>) {
  if (!selectedDevice.value) {
    ElMessage.warning('请选择设备')
    return
  }
  loading.value = true
  try {
    const { data } = await issueDeviceCommand(
      selectedDevice.value,
      commandType,
      payload,
      props.experimentId,
    )
    ElMessage.success(`指令 ${commandType} 已下发`)
    if (!props.mqttEnabled) {
      applyDeviceStatus({
        deviceId: selectedDevice.value,
        status: data.data!.status,
        commandType: data.data!.commandType,
        executedAt: data.data!.issuedAt,
      })
    }
    emit('commandIssued')
    await loadRecentCommands()
  } finally {
    loading.value = false
  }
}

async function onEmergencyStop() {
  if (!selectedDevice.value) return
  loading.value = true
  try {
    const { data } = await emergencyStopDevice(selectedDevice.value, props.experimentId)
    ElMessage.error('紧急停止已触发')
    if (!props.mqttEnabled) {
      applyDeviceStatus({
        deviceId: selectedDevice.value,
        status: data.data!.status,
        commandType: 'EMERGENCY_STOP',
        executedAt: data.data!.issuedAt,
      })
    }
    emit('commandIssued')
    await loadRecentCommands()
  } finally {
    loading.value = false
  }
}

function startPolling() {
  stopPolling()
  if (props.monitorRunning) {
    pollTimer = setInterval(() => {
      loadDevices()
      loadRecentCommands()
    }, 3000)
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

watch(
  () => props.monitorRunning,
  (run) => {
    if (run) startPolling()
    else stopPolling()
  },
)

watch(() => props.experimentId, () => {
  loadDevices()
  loadRecentCommands()
})

defineExpose({ applyDeviceStatus, loadDevices })

onMounted(async () => {
  await loadDevices()
  await loadRecentCommands()
  if (props.monitorRunning) startPolling()
})

onUnmounted(stopPolling)
</script>

<template>
  <div class="device-panel">
    <div class="section-label">设备状态</div>
    <div class="device-cards" :class="{ compact: compact }">
      <div
        v-for="d in devices.slice(0, compact ? 4 : 6)"
        :key="d.deviceId"
        class="device-card"
        :class="{ active: selectedDevice === d.deviceId, offline: !d.online }"
        @click="selectDevice(d.deviceId)"
      >
        <div class="dc-top">
          <span class="dc-name">{{ d.deviceName }}</span>
          <span class="dc-status" :class="d.online ? 'on' : 'off'">{{ d.online ? 'ONLINE' : 'OFFLINE' }}</span>
        </div>
        <div v-if="d.deviceType === 'MODEL_SHIP' && battery != null" class="dc-battery">
          电量 {{ Math.round(battery) }}%
        </div>
        <div v-else-if="d.lastCommandType" class="dc-meta">{{ d.lastCommandType }}</div>
      </div>
    </div>

    <div class="control-block">
      <div class="section-label">采集控制</div>
      <div class="console-btn-group cols-2">
        <button
          class="c-btn c-btn-primary"
          :disabled="!monitorRunning || loading"
          @click="sendCommand('START_COLLECTION')"
        >
          ▶ 启动采集
        </button>
        <button
          class="c-btn"
          :disabled="!monitorRunning || loading"
          @click="sendCommand('PAUSE_COLLECTION')"
        >
          ⏸ 暂停采集
        </button>
      </div>
    </div>

    <div class="control-block">
      <div class="section-label">航行控制</div>
      <div class="slider-block">
        <div class="slider-label">
          <span>速度</span>
          <strong>{{ speedValue }} m/s</strong>
        </div>
        <el-slider v-model="speedValue" :min="0.5" :max="3.5" :step="0.1" size="small" />
      </div>
      <div class="slider-block">
        <div class="slider-label">
          <span>航向</span>
          <strong>{{ headingValue }}°</strong>
        </div>
        <el-slider v-model="headingValue" :min="0" :max="359" :step="1" size="small" />
      </div>
      <div class="console-btn-group cols-2">
        <button
          class="c-btn"
          :disabled="!monitorRunning || loading"
          @click="sendCommand('SET_SPEED', { speed: speedValue })"
        >
          应用速度
        </button>
        <button
          class="c-btn"
          :disabled="!monitorRunning || loading"
          @click="sendCommand('SET_HEADING', { heading: headingValue })"
        >
          应用航向
        </button>
      </div>
    </div>

    <div class="control-block">
      <div class="section-label">设备控制</div>
      <div class="console-btn-group cols-2">
        <button
          class="c-btn c-btn-wave"
          :disabled="!monitorRunning || loading"
          @click="sendCommand('WAVE_MAKER_START')"
        >
          造波机启动
        </button>
        <button
          class="c-btn"
          :disabled="!monitorRunning || loading"
          @click="sendCommand('WAVE_MAKER_STOP')"
        >
          造波机停止
        </button>
      </div>
    </div>

    <div class="control-block safety">
      <button class="c-btn c-btn-emergency" :disabled="loading" @click="onEmergencyStop">
        ⛔ 紧急停止
      </button>
    </div>

    <div v-if="recentCommands.length" class="cmd-log">
      <div class="section-label">最近指令</div>
      <div v-for="cmd in recentCommands" :key="cmd.id" class="cmd-row">
        <span>{{ cmd.commandType }}</span>
        <span class="cmd-status" :class="cmd.status === 'EXECUTED' ? 'ok' : ''">{{ cmd.status }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.device-panel {
  font-size: 13px;
}
.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 8px;
}
.device-cards {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
  max-height: 160px;
  overflow-y: auto;
}
.device-cards.compact {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-height: none;
  overflow: visible;
  gap: 6px;
  margin-bottom: 10px;
}
.device-cards.compact .device-card {
  padding: 6px 8px;
}
.device-cards.compact .dc-name {
  font-size: 11px;
}
.device-card {
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  background: #fafafa;
}
.device-card:hover {
  border-color: #93c5fd;
}
.device-card.active {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.12);
}
.device-card.offline {
  opacity: 0.65;
}
.dc-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dc-name {
  font-weight: 600;
  font-size: 12px;
  color: #111827;
}
.dc-status {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  padding: 1px 6px;
  border-radius: 4px;
}
.dc-status.on {
  background: #d1fae5;
  color: #047857;
}
.dc-status.off {
  background: #f1f5f9;
  color: #64748b;
}
.dc-battery,
.dc-meta {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
}
.control-block {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f3f4f6;
}
.control-block.safety {
  border-bottom: none;
  padding-bottom: 0;
}
.console-btn-group {
  display: grid;
  gap: 6px;
}
.console-btn-group.cols-2 {
  grid-template-columns: 1fr 1fr;
}
.c-btn {
  padding: 7px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #fff;
  font-size: 12px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
}
.c-btn:hover:not(:disabled) {
  border-color: #2563eb;
  color: #2563eb;
  background: #eff6ff;
}
.c-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.c-btn-primary {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.c-btn-primary:hover:not(:disabled) {
  color: #fff;
  background: #1d4ed8;
  border-color: #1d4ed8;
}
.c-btn-wave {
  border-color: #2563eb;
  color: #2563eb;
}
.c-btn-emergency {
  width: 100%;
  padding: 10px;
  background: #dc2626;
  border: 1px solid #b91c1c;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.05em;
  border-radius: 4px;
  cursor: pointer;
}
.c-btn-emergency:hover:not(:disabled) {
  filter: brightness(1.08);
}
.c-btn-emergency:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.slider-block {
  margin-bottom: 8px;
}
.slider-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 2px;
}
.slider-label strong {
  color: #2563eb;
}
.cmd-log {
  margin-top: 8px;
}
.cmd-row {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  padding: 4px 0;
  border-bottom: 1px dashed #f1f5f9;
  font-family: ui-monospace, monospace;
}
.cmd-status {
  color: #94a3b8;
}
.cmd-status.ok {
  color: #059669;
  font-weight: 600;
}
</style>
