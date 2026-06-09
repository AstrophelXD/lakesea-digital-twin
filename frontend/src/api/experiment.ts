import request, { type ApiResponse } from './request'

export interface ExperimentTask {
  id: number
  taskNo: string
  reservationId: number
  expName: string
  status: string
  actualStartTime?: string
  actualEndTime?: string
  archiveTime?: string
}

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export function listExperiments(params?: Record<string, unknown>) {
  return request.get<ApiResponse<PageData<ExperimentTask>>>('/api/experiments', { params })
}

export function markReady(id: number) {
  return request.post<ApiResponse<ExperimentTask>>(`/api/experiments/${id}/ready`)
}

export function startExperiment(id: number) {
  return request.post<ApiResponse<ExperimentTask>>(`/api/experiments/${id}/start`)
}

export function finishExperiment(id: number) {
  return request.post<ApiResponse<ExperimentTask>>(`/api/experiments/${id}/finish`)
}

export function archiveExperiment(id: number) {
  return request.post<ApiResponse<ExperimentTask>>(`/api/experiments/${id}/archive`)
}

export interface ReplayData {
  task: ExperimentTask
  tracks: { timestamp: string; positionX: number; positionY: number; heading?: number }[]
  sensorSeries: {
    timestamp: string
    speed?: number
    battery?: number
    resistance?: number
    roll?: number
  }[]
  alarms: import('@/api/alarm').AlarmRecord[]
  alarmMarkers: {
    alarmId: number
    alarmType: string
    alarmMessage?: string
    createTime: string
    seriesIndex: number
  }[]
  files: import('@/api/file').ExperimentFile[]
  aiReport?: {
    id: number
    reportTitle?: string
    generatedTime: string
    modelName?: string
  }
  stats: {
    pointCount: number
    maxSpeed?: number
    minBattery?: number
    maxResistance?: number
    alarmCount: number
  }
}

export function getExperimentReplay(id: number) {
  return request.get<ApiResponse<ReplayData>>(`/api/experiments/${id}/replay`)
}

async function downloadExport(path: string, filename: string) {
  const token = localStorage.getItem('token')
  const base = import.meta.env.VITE_API_BASE_URL || ''
  const res = await fetch(`${base}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    const err = await res.json().catch(() => null)
    throw new Error(err?.message || 'Export failed')
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function exportSensorCsv(experimentId: number) {
  return downloadExport(
    `/api/experiments/${experimentId}/export/sensor-csv`,
    `experiment_${experimentId}_sensor.csv`,
  )
}

export function exportTrackJson(experimentId: number) {
  return downloadExport(
    `/api/experiments/${experimentId}/export/track-json`,
    `experiment_${experimentId}_track.json`,
  )
}

export function exportAiReport(experimentId: number, format: 'markdown' | 'html' = 'markdown') {
  return downloadExport(
    `/api/experiments/${experimentId}/export/ai-report?fmt=${format}`,
    `experiment_${experimentId}_ai_report.${format === 'html' ? 'html' : 'md'}`,
  )
}
