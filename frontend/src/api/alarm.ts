import request, { type ApiResponse } from './request'

export interface AlarmRecord {
  id: number
  experimentId: number
  alarmType: string
  alarmLevel?: string
  alarmMessage?: string
  handleStatus: string
  handleComment?: string
  createTime: string
}

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export function listAlarms(params?: Record<string, unknown>) {
  return request.get<ApiResponse<PageData<AlarmRecord>>>('/api/alarms', { params })
}

export function handleAlarm(id: number, handleStatus: string, comment?: string) {
  return request.post<ApiResponse<AlarmRecord>>(`/api/alarms/${id}/handle`, {
    handleStatus,
    comment,
  })
}

export const ALARM_TYPE_LABELS: Record<string, string> = {
  NEAR_BOUNDARY: '接近边界',
  OUT_OF_BOUNDARY: '越界',
  LOW_BATTERY: '电量过低',
  SPEED_LIMIT: '超速',
  DATA_SPIKE: '数据突变',
}
