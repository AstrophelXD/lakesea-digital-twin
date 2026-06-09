import request, { type ApiResponse } from './request'

export interface CvTrackResult {
  experimentId: number
  cameraId: string
  timestamp: string
  bbox: number[]
  centerX: number
  centerY: number
  poolX: number
  poolY: number
  confidence: number
  source: string
}

export interface CvTrackStatus {
  enabled: boolean
  opencvAvailable: boolean
  tracking: boolean
  latest?: CvTrackResult | null
}

export function getCvStatus(experimentId: number) {
  return request.get<ApiResponse<CvTrackStatus>>(`/api/cv/${experimentId}/status`)
}

export function getCvLatestTrack(experimentId: number) {
  return request.get<ApiResponse<CvTrackResult | null>>(`/api/cv/${experimentId}/track`)
}

export function startCvTracking(experimentId: number) {
  return request.post<ApiResponse<CvTrackStatus>>(`/api/cv/${experimentId}/start`)
}

export function stopCvTracking(experimentId: number) {
  return request.post<ApiResponse<CvTrackStatus>>(`/api/cv/${experimentId}/stop`)
}
