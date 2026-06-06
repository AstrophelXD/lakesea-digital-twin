<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import {
  getAlarmTrend,
  getDashboardSummary,
  getReservationStatus,
  getResourceStatus,
  type DashboardSummary,
} from '@/api/dashboard'
import { useUserStore } from '@/stores/user'
import { statusLabel } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()
const summary = ref<DashboardSummary | null>(null)
const loading = ref(false)

const reservationChartRef = ref<HTMLDivElement>()
const resourceChartRef = ref<HTMLDivElement>()
const alarmChartRef = ref<HTMLDivElement>()

let reservationChart: echarts.ECharts | null = null
let resourceChart: echarts.ECharts | null = null
let alarmChart: echarts.ECharts | null = null

const statCards = [
  { key: 'todayReservations', label: '今日预约数', color: '#0f766e', icon: '📅' },
  { key: 'runningExperiments', label: '运行中试验', color: '#2563eb', icon: '🔬' },
  { key: 'availableResources', label: '可用资源数', color: '#7c3aed', icon: '📦' },
  { key: 'pendingAlarms', label: '待处理告警', color: '#dc2626', icon: '🔔' },
] as const

const quickLinks = [
  { label: '试验预约', path: '/reservations', type: 'primary' as const },
  { label: '数字孪生监控', path: '/monitor', type: 'success' as const },
  { label: 'AI 分析报告', path: '/ai-report', type: 'warning' as const },
]

function renderPie(
  el: HTMLDivElement | undefined,
  data: { name: string; value: number }[],
  title: string,
) {
  if (!el) return null
  const chart = echarts.init(el)
  chart.setOption({
    title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        data,
        label: { formatter: '{b}: {c}' },
      },
    ],
  })
  return chart
}

function renderLine(el: HTMLDivElement | undefined, dates: string[], counts: number[]) {
  if (!el) return null
  const chart = echarts.init(el)
  chart.setOption({
    title: { text: '最近 7 天告警趋势', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'line', data: counts, smooth: true, areaStyle: { opacity: 0.15 } }],
  })
  return chart
}

async function load() {
  loading.value = true
  try {
    const [sumRes, resStatus, resourceStatus, alarmTrend] = await Promise.all([
      getDashboardSummary(),
      getReservationStatus(),
      getResourceStatus(),
      getAlarmTrend(),
    ])
    summary.value = sumRes.data.data!

    reservationChart?.dispose()
    resourceChart?.dispose()
    alarmChart?.dispose()

    reservationChart = renderPie(
      reservationChartRef.value,
      (resStatus.data.data || []).map((d) => ({
        name: statusLabel(d.status),
        value: d.count,
      })),
      '预约状态分布',
    )
    resourceChart = renderPie(
      resourceChartRef.value,
      (resourceStatus.data.data || []).map((d) => ({
        name: statusLabel(d.status),
        value: d.count,
      })),
      '资源状态分布',
    )
    const trend = alarmTrend.data.data || []
    alarmChart = renderLine(
      alarmChartRef.value,
      trend.map((t) => t.date.slice(5)),
      trend.map((t) => t.count),
    )
  } finally {
    loading.value = false
  }
}

function handleResize() {
  reservationChart?.resize()
  resourceChart?.resize()
  alarmChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  reservationChart?.dispose()
  resourceChart?.dispose()
  alarmChart?.dispose()
})
</script>

<template>
  <div v-loading="loading" class="dashboard">
    <div class="welcome-bar">
      <div>
        <h2>欢迎，{{ userStore.user?.realName }}</h2>
        <p class="subtitle">校园湖海试验场数字孪生全景监控与数据管理系统</p>
      </div>
      <el-tag v-if="summary" type="info" size="large" effect="plain">
        当前数据库：{{ summary.databaseType }}
      </el-tag>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col v-for="card in statCards" :key="card.key" :xs="12" :sm="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" :style="{ color: card.color }">{{ card.icon }}</div>
          <div class="stat-value" :style="{ color: card.color }">
            {{ summary ? summary[card.key] : '-' }}
          </div>
          <div class="stat-label">{{ card.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="quick-card">
      <template #header>快速进入演示链路</template>
      <el-space wrap>
        <el-button
          v-for="link in quickLinks"
          :key="link.path"
          :type="link.type"
          @click="router.push(link.path)"
        >
          {{ link.label }}
        </el-button>
      </el-space>
    </el-card>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="8">
        <el-card shadow="never"><div ref="reservationChartRef" class="chart-box" /></el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never"><div ref="resourceChartRef" class="chart-box" /></el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never"><div ref="alarmChartRef" class="chart-box" /></el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1280px;
}

.welcome-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.welcome-bar h2 {
  margin: 0 0 4px;
  font-size: 22px;
  color: #111827;
}

.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  margin-bottom: 12px;
}

.stat-icon {
  font-size: 28px;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  color: #6b7280;
  font-size: 13px;
  margin-top: 4px;
}

.quick-card {
  margin-bottom: 16px;
}

.chart-row {
  margin-bottom: 16px;
}

.chart-box {
  height: 280px;
}
</style>
