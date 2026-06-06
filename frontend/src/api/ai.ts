import request, { type ApiResponse } from './request'

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
  analysisMode?: string
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
