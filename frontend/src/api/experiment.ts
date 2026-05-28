import request, { type ApiResponse } from './request'

export interface ExperimentTask {
  id: number
  taskNo: string
  reservationId: number
  expName: string
  status: string
  actualStartTime?: string
  actualEndTime?: string
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
  files: import('@/api/file').ExperimentFile[]
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
