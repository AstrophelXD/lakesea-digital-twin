<script setup lang="ts">
import { computed } from 'vue'
import type { SystemHealthStatus } from '@/api/health'

const props = defineProps<{
  wsStatus: 'connected' | 'reconnecting' | 'disconnected'
  monitorRunning: boolean
  health: SystemHealthStatus | null
  wsLatencyMs: number | null
  mqttLatencyMs: number | null
  dataSourceLabel: string
}>()

const wsLabel = computed(() => {
  const map = { connected: '已连接', reconnecting: '重连中', disconnected: '已断开' }
  return map[props.wsStatus]
})

const endToEndLatency = computed(() => {
  if (props.wsLatencyMs == null) return null
  return props.wsLatencyMs + (props.mqttLatencyMs ?? 0)
})
</script>

<template>
  <el-card shadow="never" class="status-bar">
    <div class="status-row">
      <el-tag :type="wsStatus === 'connected' ? 'success' : wsStatus === 'reconnecting' ? 'warning' : 'info'">
        WebSocket {{ wsLabel }}
      </el-tag>
      <el-tag v-if="health" :type="health.mqttBroker === 'UP' ? 'success' : health.mqttBroker === 'DISABLED' ? 'info' : 'danger'">
        MQTT {{ health.mqttBroker === 'UP' ? '已连接' : health.mqttBroker === 'DISABLED' ? '未启用' : '未连接' }}
      </el-tag>
      <el-tag v-if="health" :type="health.videoStream === 'UP' ? 'success' : 'danger'">
        视频流 {{ health.videoStream === 'UP' ? '正常' : '异常' }}
      </el-tag>
      <el-tag v-if="health" :type="health.edgeAgent === 'UP' ? 'success' : 'warning'">
        边缘端 {{ health.edgeAgent === 'UP' ? '在线' : '离线' }}
      </el-tag>
      <el-tag :type="monitorRunning ? 'success' : 'warning'">
        监控 {{ monitorRunning ? '运行中' : '已停止' }}
      </el-tag>
      <el-tag type="primary">{{ dataSourceLabel }}</el-tag>
      <el-tag v-if="wsLatencyMs != null" type="info">
        WebSocket 延迟 {{ wsLatencyMs }} ms
      </el-tag>
      <el-tag v-if="endToEndLatency != null" type="info">
        端到端延迟 {{ endToEndLatency }} ms
      </el-tag>
      <el-tag v-if="health" type="info">
        数据刷新 {{ health.dataRefreshHz }} Hz
      </el-tag>
    </div>
    <div v-if="health" class="health-detail">
      <span>后端：{{ health.backend === 'UP' ? '正常' : '异常' }}</span>
      <span>数据库：{{ health.database === 'UP' ? '正常' : '异常' }} ({{ health.databaseType }})</span>
      <span v-if="health.latestDataTime">最近数据：{{ health.latestDataTime }}</span>
    </div>
  </el-card>
</template>

<style scoped>
.status-bar {
  margin-bottom: 12px;
}
.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.health-detail {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: #6b7280;
}
</style>
