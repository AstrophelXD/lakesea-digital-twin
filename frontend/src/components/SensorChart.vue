<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { MonitorFrame } from '@/api/monitor'

const props = defineProps<{
  frames: MonitorFrame[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!chart) return
  const labels = props.frames.map((f) => f.timestamp.slice(11, 19))
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['速度', '电量', '阻力'], textStyle: { color: '#64748b', fontSize: 11 } },
    grid: { left: 48, right: 24, top: 32, bottom: 24 },
    xAxis: {
      type: 'category',
      data: labels,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
    },
    yAxis: [
      { type: 'value', name: '速度/阻力', scale: true, splitLine: { lineStyle: { color: '#f1f5f9' } } },
      { type: 'value', name: '电量%', max: 100, min: 0, splitLine: { show: false } },
    ],
    series: [
      { name: '速度', type: 'line', data: props.frames.map((f) => f.speed), smooth: true, lineStyle: { color: '#0284c7' }, areaStyle: { color: 'rgba(2,132,199,0.08)' } },
      {
        name: '电量',
        type: 'line',
        yAxisIndex: 1,
        data: props.frames.map((f) => f.battery),
        smooth: true,
        lineStyle: { color: '#2563eb' },
        areaStyle: { color: 'rgba(37, 99, 235, 0.08)' },
      },
      { name: '阻力', type: 'line', data: props.frames.map((f) => f.resistance), smooth: true, lineStyle: { color: '#64748b' } },
    ],
  })
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    render()
    window.addEventListener('resize', () => chart?.resize())
  }
})

watch(() => props.frames, render, { deep: true })

onUnmounted(() => {
  chart?.dispose()
})
</script>

<template>
  <div ref="chartRef" class="sensor-chart" />
</template>

<style scoped>
.sensor-chart {
  width: 100%;
  height: 280px;
}
</style>
