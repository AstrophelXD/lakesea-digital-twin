import request, { type ApiResponse } from './request'

export interface DashboardSummary {
  todayReservations: number
  runningExperiments: number
  availableResources: number
  pendingAlarms: number
  databaseType: string
}

export interface StatusCount {
  status: string
  count: number
}

export interface TrendPoint {
  date: string
  count: number
}

export function getDashboardSummary() {
  return request.get<ApiResponse<DashboardSummary>>('/api/dashboard/summary')
}

export function getReservationStatus() {
  return request.get<ApiResponse<StatusCount[]>>('/api/dashboard/reservation-status')
}

export function getResourceStatus() {
  return request.get<ApiResponse<StatusCount[]>>('/api/dashboard/resource-status')
}

export function getAlarmTrend() {
  return request.get<ApiResponse<TrendPoint[]>>('/api/dashboard/alarm-trend')
}

export function getDbHealth() {
  return request.get<ApiResponse<{
    databaseType: string
    connected: boolean
    tableCounts: Record<string, number>
    coreTableTotal: number
  }>>('/api/health/db')
}
