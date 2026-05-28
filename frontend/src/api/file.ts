import request, { type ApiResponse } from './request'

export interface ExperimentFile {
  id: number
  experimentId: number
  fileName: string
  fileType?: string
  uploadTime: string
}

export function listFiles(experimentId: number) {
  return request.get<ApiResponse<ExperimentFile[]>>('/api/files', {
    params: { experimentId },
  })
}

export function uploadFile(experimentId: number, file: File, fileType?: string) {
  const form = new FormData()
  form.append('experimentId', String(experimentId))
  form.append('file', file)
  if (fileType) form.append('fileType', fileType)
  return request.post<ApiResponse<ExperimentFile>>('/api/files/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export async function downloadFile(fileId: number, fileName: string) {
  const token = localStorage.getItem('token')
  const base = import.meta.env.VITE_API_BASE_URL || ''
  const res = await fetch(`${base}/api/files/${fileId}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error('下载失败')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.click()
  URL.revokeObjectURL(url)
}
