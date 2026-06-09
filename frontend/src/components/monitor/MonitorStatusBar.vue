<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { SystemHealthStatus } from '@/api/health'
import type { ExperimentTask } from '@/api/experiment'

const props = defineProps<{
  wsStatus: 'connected' | 'reconnecting' | 'disconnected'
  monitorRunning: boolean
  health: SystemHealthStatus | null
  wsLatencyMs: number | null
  dataSourceLabel: string
  experiment?: ExperimentTask | null
}>()

const nowStr = ref('')
let clockTimer: ReturnType<typeof setInterval> | null = null

const experimentTitle = computed(() => {
  if (props.experiment) return `${props.experiment.taskNo} · ${props.experiment.expName}`
  return '演示试验'
})

const wsLabel = computed(() => {
  const map = { connected: '已连接', reconnecting: '重连中', disconnected: '已断开' }
  return map[props.wsStatus]
})

const wsTagType = computed(() => {
  if (props.wsStatus === 'connected') return 'success'
  if (props.wsStatus === 'reconnecting') return 'warning'
  return 'info'
})

function tickClock() {
  const d = new Date()
  nowStr.value = d.toLocaleTimeString('zh-CN', { hour12: false })
}

onMounted(() => {
  tickClock()
  clockTimer = setInterval(tickClock, 1000)
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<template>
  <div class="status-bar">
    <div class="status-left">
      <div class="exp-badge">
        <span class="exp-dot" :class="{ live: monitorRunning }" />
        <span class="exp-name">{{ experimentTitle }}</span>
      </div>
      <div class="tag-row">
        <el-tag size="small" :type="wsTagType" effect="plain" round>
          WS {{ wsLabel }}
        </el-tag>
        <el-tag
          v-if="health"
          size="small"
          :type="health.mqttBroker === 'UP' ? 'success' : health.mqttBroker === 'DISABLED' ? 'info' : 'danger'"
          effect="plain"
          round
        >
          MQTT {{ health.mqttBroker === 'UP' ? '正常' : health.mqttBroker === 'DISABLED' ? '未启用' : '断开' }}
        </el-tag>
        <el-tag
          v-if="health"
          size="small"
          :type="health.videoStream === 'UP' ? 'success' : 'danger'"
          effect="plain"
          round
        >
          视频 {{ health.videoStream === 'UP' ? '正常' : '异常' }}
        </el-tag>
        <el-tag
          v-if="health"
          size="small"
          :type="health.edgeAgent === 'UP' ? 'success' : 'warning'"
          effect="plain"
          round
        >
          边缘端 {{ health.edgeAgent === 'UP' ? '在线' : '离线' }}
        </el-tag>
        <el-tag size="small" :type="monitorRunning ? 'success' : 'warning'" effect="plain" round>
          {{ monitorRunning ? '运行中' : '待命' }}
        </el-tag>
        <el-tag v-if="wsLatencyMs != null" size="small" type="info" effect="plain" round>
          延迟 {{ wsLatencyMs }} ms
        </el-tag>
        <el-tag size="small" effect="plain" round>{{ dataSourceLabel }}</el-tag>
      </div>
    </div>
    <div class="status-right">
      <span class="clock">{{ nowStr }}</span>
    </div>
  </div>
</template>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.status-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}
.exp-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 14px;
  border-right: 1px solid #e2e8f0;
}
.exp-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
}
.exp-dot.live {
  background: #14b8a6;
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.25);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.exp-name {
  font-size: 14px;
  font-weight: 600;
  color: #0f766e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 280px;
}
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.status-right {
  flex-shrink: 0;
}
.clock {
  font-family: ui-monospace, 'Cascadia Code', monospace;
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  letter-spacing: 0.05em;
}
</style>
