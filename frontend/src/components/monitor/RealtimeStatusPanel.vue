<script setup lang="ts">
import { computed } from 'vue'
import type { MonitorFrame } from '@/api/monitor'
import type { AlarmRecord } from '@/api/alarm'
import type { SystemHealthStatus } from '@/api/health'
import { ALARM_TYPE_LABELS } from '@/api/alarm'

const props = defineProps<{
  latestFrame: MonitorFrame | null
  alarms: AlarmRecord[]
  health: SystemHealthStatus | null
  onlineDeviceCount: number
  totalDeviceCount: number
  monitorRunning: boolean
  compact?: boolean
}>()

const speed = computed(() => props.latestFrame?.speed ?? null)
const battery = computed(() => props.latestFrame?.battery ?? null)
const alarmCount = computed(() => props.alarms.length)
const pendingAlarms = computed(() => props.alarms.filter((a) => a.handleStatus === 'PENDING').length)

const kpiCards = computed(() => [
  {
    label: '在线设备',
    value: `${props.onlineDeviceCount}/${props.totalDeviceCount}`,
    unit: '',
    color: '#2563eb',
    bg: '#eff6ff',
  },
  {
    label: '当前速度',
    value: speed.value != null ? speed.value.toFixed(1) : '—',
    unit: speed.value != null ? 'm/s' : '',
    color: '#0284c7',
    bg: '#f0f9ff',
  },
  {
    label: '电量',
    value: battery.value != null ? Math.round(battery.value) : '—',
    unit: battery.value != null ? '%' : '',
    color: battery.value != null && battery.value < 20 ? '#dc2626' : '#059669',
    bg: battery.value != null && battery.value < 20 ? '#fef2f2' : '#f0fdf4',
  },
  {
    label: '告警数',
    value: String(alarmCount.value),
    unit: pendingAlarms.value ? `(${pendingAlarms.value} 待处理)` : '',
    color: alarmCount.value > 0 ? '#ea580c' : '#64748b',
    bg: alarmCount.value > 0 ? '#fff7ed' : '#f8fafc',
  },
  {
    label: '视频流',
    value: props.health?.videoStream === 'UP' ? '正常' : '—',
    unit: '',
    color: '#0369a1',
    bg: '#f0f9ff',
  },
  {
    label: '边缘端',
    value: props.health?.edgeAgent === 'UP' ? '在线' : '离线',
    unit: '',
    color: props.health?.edgeAgent === 'UP' ? '#2563eb' : '#9ca3af',
    bg: props.health?.edgeAgent === 'UP' ? '#eff6ff' : '#f9fafb',
  },
])

function alarmLevelType(level?: string) {
  if (level === 'HIGH') return 'danger'
  if (level === 'MEDIUM') return 'warning'
  return 'info'
}

const systemItems = computed(() => {
  if (!props.health) return []
  return [
    { label: '后端', ok: props.health.backend === 'UP' },
    { label: '数据库', ok: props.health.database === 'UP', extra: props.health.databaseType },
    { label: 'MQTT', ok: props.health.mqttBroker === 'UP' || props.health.mqttBroker === 'DISABLED', text: props.health.mqttBroker },
    { label: '刷新率', ok: true, text: `${props.health.dataRefreshHz} Hz` },
  ]
})
</script>

<template>
  <div class="realtime-panel" :class="{ compact }">
    <!-- KPI 卡片 -->
    <div class="kpi-grid">
      <div
        v-for="card in kpiCards"
        :key="card.label"
        class="kpi-card"
        :style="{ background: card.bg }"
      >
        <div class="kpi-label">{{ card.label }}</div>
        <div class="kpi-value" :style="{ color: card.color }">
          {{ card.value }}<small v-if="card.unit">{{ card.unit }}</small>
        </div>
      </div>
    </div>

    <!-- 实时指标 -->
    <div v-if="latestFrame" class="metrics-strip">
      <span>横摇 {{ latestFrame.roll }}°</span>
      <span>纵摇 {{ latestFrame.pitch }}°</span>
      <span>阻力 {{ latestFrame.resistance }} N</span>
    </div>

    <!-- 告警 -->
    <div class="alarm-block">
      <div class="block-head">
        <span class="block-title">实时告警</span>
        <el-badge v-if="alarmCount" :value="alarmCount" type="danger" />
      </div>
      <div v-if="!alarms.length" class="alarm-empty">
        <div class="empty-icon">✓</div>
        <div class="empty-text">当前无活跃告警</div>
        <div class="empty-sub">系统运行正常，持续监测中</div>
      </div>
      <div v-else class="alarm-list">
        <div v-for="a in alarms.slice(0, 6)" :key="a.id" class="alarm-row">
          <el-tag size="small" :type="alarmLevelType(a.alarmLevel)">
            {{ ALARM_TYPE_LABELS[a.alarmType] || a.alarmType }}
          </el-tag>
          <span class="alarm-msg">{{ a.alarmMessage }}</span>
          <span class="alarm-time">{{ a.createTime?.slice(11, 19) }}</span>
        </div>
      </div>
    </div>

    <!-- 系统状态 -->
    <div class="system-block">
      <div class="block-title">系统状态</div>
      <div class="system-list">
        <div v-for="item in systemItems" :key="item.label" class="sys-row">
          <span>{{ item.label }}</span>
          <span v-if="item.text" class="sys-val">{{ item.text }}</span>
          <span v-else class="sys-dot" :class="item.ok ? 'ok' : 'err'" />
        </div>
        <div v-if="health?.latestDataTime" class="sys-row muted">
          <span>最近数据</span>
          <span class="sys-val">{{ health.latestDataTime }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.realtime-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
}
.realtime-panel.compact .kpi-grid {
  grid-template-columns: 1fr 1fr 1fr;
  gap: 6px;
}
.realtime-panel.compact .kpi-card {
  padding: 7px 8px;
}
.realtime-panel.compact .kpi-value {
  font-size: 16px;
}
.realtime-panel.compact .alarm-block,
.realtime-panel.compact .system-block {
  padding: 8px 10px;
}
.realtime-panel.compact .alarm-list {
  max-height: 120px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.kpi-card {
  padding: 10px 12px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}
.kpi-label {
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 4px;
}
.kpi-value {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.2;
  font-family: ui-monospace, monospace;
}
.kpi-value small {
  font-size: 11px;
  font-weight: 500;
  margin-left: 2px;
}
.metrics-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 10px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 12px;
  color: #374151;
  font-family: monospace;
}
.alarm-block,
.system-block {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 10px 12px;
  background: #fafafa;
}
.block-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.block-title {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}
.alarm-empty {
  text-align: center;
  padding: 16px 8px;
}
.empty-icon {
  width: 36px;
  height: 36px;
  margin: 0 auto 8px;
  border-radius: 50%;
  background: #dbeafe;
  color: #2563eb;
  font-size: 18px;
  line-height: 36px;
  font-weight: 700;
}
.empty-text {
  font-size: 13px;
  color: #475569;
  font-weight: 500;
}
.empty-sub {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 4px;
}
.alarm-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 180px;
  overflow-y: auto;
}
.alarm-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #f1f5f9;
  font-size: 12px;
}
.alarm-msg {
  flex: 1;
  color: #334155;
  line-height: 1.4;
}
.alarm-time {
  font-size: 10px;
  color: #94a3b8;
  font-family: monospace;
  flex-shrink: 0;
}
.system-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sys-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  padding: 3px 0;
  color: #475569;
}
.sys-row.muted {
  color: #94a3b8;
  font-size: 11px;
}
.sys-val {
  font-family: monospace;
  font-size: 11px;
}
.sys-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.sys-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.25);
}
.sys-dot.err {
  background: #ef4444;
}
</style>
