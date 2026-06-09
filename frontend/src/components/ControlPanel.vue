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
}>()

const emit = defineEmits<{
  commandIssued: []
}>()

const devices = ref<DeviceInfo[]>([])
const selectedDevice = ref('')
const speedValue = ref(1.5)
const headingValue = ref(45)
const loading = ref(false)
const recentCommands = ref<DeviceCommand[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

const selectedDeviceInfo = ref<DeviceInfo | null>(null)

async function loadDevices() {
  const { data } = await listDevices(props.experimentId)
  devices.value = data.data ?? []
  if (!selectedDevice.value && devices.value.length) {
    selectedDevice.value = devices.value[0].deviceId
  }
  selectedDeviceInfo.value =
    devices.value.find((d) => d.deviceId === selectedDevice.value) ?? null
}

async function loadRecentCommands() {
  if (!selectedDevice.value) return
  const { data } = await listDeviceCommands(selectedDevice.value, props.experimentId)
  recentCommands.value = (data.data?.items ?? []).slice(0, 5)
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
  if (selectedDevice.value === event.deviceId) {
    selectedDeviceInfo.value = devices.value[idx]
    loadRecentCommands()
  }
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

watch(selectedDevice, () => {
  selectedDeviceInfo.value =
    devices.value.find((d) => d.deviceId === selectedDevice.value) ?? null
  loadRecentCommands()
})

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
  <div class="control-panel">
    <div class="section-title">设备列表</div>
    <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 100%; margin-bottom: 10px">
      <el-option
        v-for="d in devices"
        :key="d.deviceId"
        :label="`${d.deviceName} (${d.status})`"
        :value="d.deviceId"
      >
        <span>{{ d.deviceName }}</span>
        <el-tag
          size="small"
          :type="d.online ? 'success' : 'info'"
          style="margin-left: 8px"
        >
          {{ d.online ? '在线' : '离线' }}
        </el-tag>
      </el-option>
    </el-select>

    <div v-if="selectedDeviceInfo" class="device-status-card">
      <div class="status-row">
        <span>运行状态</span>
        <el-tag size="small" :type="selectedDeviceInfo.online ? 'success' : 'warning'">
          {{ selectedDeviceInfo.status }}
        </el-tag>
      </div>
      <div v-if="selectedDeviceInfo.lastCommandType" class="status-row">
        <span>最近指令</span>
        <span class="mono">{{ selectedDeviceInfo.lastCommandType }}</span>
      </div>
      <div v-if="selectedDeviceInfo.lastAckAt" class="status-row">
        <span>回执时间</span>
        <span class="mono">{{ selectedDeviceInfo.lastAckAt }}</span>
      </div>
      <div v-if="mqttEnabled && selectedDeviceInfo.ackStatus" class="status-row">
        <span>MQTT 回执</span>
        <el-tag size="small" type="success">{{ selectedDeviceInfo.ackStatus }}</el-tag>
      </div>
    </div>

    <div class="section-title">控制面板</div>
    <div class="btn-grid">
      <el-button
        type="primary"
        size="small"
        :loading="loading"
        :disabled="!monitorRunning"
        @click="sendCommand('START_COLLECTION')"
      >
        启动采集
      </el-button>
      <el-button
        size="small"
        :loading="loading"
        :disabled="!monitorRunning"
        @click="sendCommand('PAUSE_COLLECTION')"
      >
        暂停采集
      </el-button>
      <el-button
        size="small"
        :loading="loading"
        :disabled="!monitorRunning"
        @click="sendCommand('SET_SPEED', { speed: speedValue })"
      >
        设置速度
      </el-button>
      <el-button
        size="small"
        :loading="loading"
        :disabled="!monitorRunning"
        @click="sendCommand('SET_HEADING', { heading: headingValue })"
      >
        设置航向
      </el-button>
      <el-button
        size="small"
        :loading="loading"
        :disabled="!monitorRunning"
        @click="sendCommand('WAVE_MAKER_START')"
      >
        造波机启动
      </el-button>
      <el-button
        size="small"
        :loading="loading"
        :disabled="!monitorRunning"
        @click="sendCommand('WAVE_MAKER_STOP')"
      >
        造波机停止
      </el-button>
    </div>

    <div class="sliders">
      <div class="slider-row">
        <span>速度 {{ speedValue }} m/s</span>
        <el-slider v-model="speedValue" :min="0.5" :max="3.5" :step="0.1" size="small" />
      </div>
      <div class="slider-row">
        <span>航向 {{ headingValue }}°</span>
        <el-slider v-model="headingValue" :min="0" :max="359" :step="1" size="small" />
      </div>
    </div>

    <el-button
      type="danger"
      style="width: 100%; margin-top: 10px"
      :loading="loading"
      @click="onEmergencyStop"
    >
      紧急停止
    </el-button>

    <div v-if="recentCommands.length" class="cmd-log">
      <div class="section-title">指令日志</div>
      <div v-for="cmd in recentCommands" :key="cmd.id" class="cmd-item">
        <span class="mono">{{ cmd.commandType }}</span>
        <el-tag size="small" :type="cmd.status === 'EXECUTED' ? 'success' : 'info'">
          {{ cmd.status }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<style scoped>
.control-panel {
  font-size: 13px;
}
.section-title {
  font-weight: 600;
  margin-bottom: 8px;
  margin-top: 4px;
}
.device-status-card {
  background: #f8fafc;
  border-radius: 8px;
  padding: 8px 10px;
  margin-bottom: 12px;
}
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  margin-bottom: 4px;
}
.mono {
  font-family: ui-monospace, monospace;
  font-size: 11px;
  color: #475569;
}
.btn-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.sliders {
  margin-top: 12px;
}
.slider-row {
  margin-bottom: 8px;
}
.slider-row span {
  font-size: 12px;
  color: #64748b;
}
.cmd-log {
  margin-top: 14px;
}
.cmd-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 12px;
}
</style>
