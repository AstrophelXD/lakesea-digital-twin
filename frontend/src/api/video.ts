import request, { type ApiResponse } from './request'

export interface VideoStreamConfig {
  mode: string
  cameraId: string
  streamUrl?: string | null
  fileUrl?: string | null
  mjpegUrl?: string | null
  status: string
}

export interface VideoRecord {
  id: number
  experimentId: number
  cameraId: string
  streamUrl?: string | null
  filePath?: string | null
  startTime?: string | null
  endTime?: string | null
  status: string
  createTime?: string | null
}

export function getVideoConfig(experimentId: number) {
  return request.get<ApiResponse<VideoStreamConfig>>(`/api/video/${experimentId}/config`)
}

export function startVideoRecording(experimentId: number, cameraId = 'CAM-001', mode = 'file') {
  return request.post<ApiResponse<VideoRecord>>(`/api/video/${experimentId}/start`, {
    cameraId,
    mode,
  })
}

export function stopVideoRecording(experimentId: number) {
  return request.post<ApiResponse<VideoRecord>>(`/api/video/${experimentId}/stop`)
}

export function getVideoRecords(experimentId: number) {
  return request.get<ApiResponse<{ items: VideoRecord[]; total: number }>>(
    `/api/video/${experimentId}/records`,
  )
}

export function buildVideoAssetUrl(path: string) {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  const token = localStorage.getItem('token')
  const sep = path.includes('?') ? '&' : '?'
  return token ? `${base}${path}${sep}token=${encodeURIComponent(token)}` : `${base}${path}`
}
