import request, { type ApiResponse } from './request'

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface ReportSection {
  title: string
  content: string
}

export interface AiReport {
  id: number
  experimentId: number
  reportTitle?: string
  summaryText?: string
  analysisText?: string
  modelName?: string
  generatedTime: string
  mock?: boolean
  analysisType?: string
  analysisTypeLabel?: string
  analysisMode?: string
  sections?: ReportSection[]
}

export interface AiMode {
  analysisMode: string
  mockAi: boolean
  hasApiKey: boolean
  modelName: string
}

export interface ExperimentDataSummary {
  experimentId: number
  taskNo: string
  expName: string
  status: string
  pointCount: number
  maxSpeed?: number
  minBattery?: number
  maxResistance?: number
  maxRoll?: number
  alarmCount: number
  alarmSummary: string
  alarms: { alarmType: string; alarmMessage?: string; createTime: string }[]
  actualStartTime?: string
  actualEndTime?: string
}

export interface AiCallLog {
  id: number
  experimentId?: number
  analysisType?: string
  modelName?: string
  isMock: boolean
  success: boolean
  durationMs?: number
  tokenUsed?: number
  errorMessage?: string
  callTime: string
}

export interface AiReportListItem {
  id: number
  experimentId: number
  reportTitle?: string
  analysisType?: string
  modelName?: string
  generatedTime: string
}

export function getAiMode() {
  return request.get<ApiResponse<AiMode>>('/api/ai/mode')
}

export function getExperimentDataSummary(experimentId: number) {
  return request.get<ApiResponse<ExperimentDataSummary>>(
    `/api/ai/reports/summary/${experimentId}`,
  )
}

export function listAiCallLogs(params?: {
  experimentId?: number
  page?: number
  pageSize?: number
}) {
  return request.get<ApiResponse<PageData<AiCallLog>>>('/api/ai/logs', { params })
}

export function listAiReports(params?: { page?: number; pageSize?: number }) {
  return request.get<ApiResponse<PageData<AiReportListItem>>>('/api/ai/reports/list', {
    params,
  })
}

export function generateAiReport(experimentId: number, analysisType = 'OVERVIEW') {
  return request.post<ApiResponse<AiReport>>('/api/ai/reports/generate', {
    experimentId,
    analysisType,
  })
}

export function getAiReport(experimentId: number) {
  return request.get<ApiResponse<AiReport>>(`/api/ai/reports/${experimentId}`)
}

export function deleteAiReport(reportId: number) {
  return request.delete<ApiResponse<null>>(`/api/ai/reports/${reportId}`)
}
