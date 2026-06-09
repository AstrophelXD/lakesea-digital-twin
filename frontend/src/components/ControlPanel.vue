<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  emergencyStopDevice,
  issueDeviceCommand,
  listDevices,
  type DeviceInfo,
} from '@/api/device'

const props = defineProps<{
  experimentId?: number
  monitorRunning?: boolean
}>()

const emit = defineEmits<{
  commandIssued: []
}>()

const devices = ref<DeviceInfo[]>([])
const selectedDevice = ref('')
const speedValue = ref(1.5)
const headingValue = ref(45)
const loading = ref(false)

async function loadDevices() {
  const { data } = await listDevices(props.experimentId)
  devices.value = data.data ?? []
  if (!selectedDevice.value && devices.value.length) {
    selectedDevice.value = devices.value[0].deviceId
  }
}

async function sendCommand(commandType: string, payload?: Record<string, unknown>) {
  if (!selectedDevice.value) {
    ElMessage.warning('请选择设备')
    return
  }
  loading.value = true
  try {
    await issueDeviceCommand(
      selectedDevice.value,
      commandType,
      payload,
      props.experimentId,
    )
    ElMessage.success(`指令 ${commandType} 已下发`)
    emit('commandIssued')
  } finally {
    loading.value = false
  }
}

async function onEmergencyStop() {
  if (!selectedDevice.value) return
  loading.value = true
  try {
    await emergencyStopDevice(selectedDevice.value, props.experimentId)
    ElMessage.error('紧急停止已触发')
    emit('commandIssued')
  } finally {
    loading.value = false
  }
}

watch(() => props.experimentId, loadDevices)
onMounted(loadDevices)
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
</style>
