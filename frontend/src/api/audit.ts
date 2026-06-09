import request, { type ApiResponse } from './request'

export interface OperationLog {
  id: number
  userId?: number
  username?: string
  module: string
  moduleLabel?: string
  action: string
  actionLabel?: string
  targetType?: string
  targetId?: number
  detail?: string
  ipAddress?: string
  success: boolean
  createTime: string
}

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface AuditMeta {
  modules: { value: string; label: string }[]
  actions: { value: string; label: string }[]
}

export function listOperationLogs(params?: {
  module?: string
  action?: string
  userId?: number
  keyword?: string
  success?: boolean
  page?: number
  pageSize?: number
}) {
  return request.get<ApiResponse<PageData<OperationLog>>>('/api/audit/logs', { params })
}

export function getAuditMeta() {
  return request.get<ApiResponse<AuditMeta>>('/api/audit/meta')
}
