import request, { type ApiResponse } from './request'

export interface SystemHealthStatus {
  backend: string
  database: string
  databaseType: string
  mqttBroker: string
  videoStream: string
  edgeAgent: string
  mqttEnabled: boolean
  mqttConnected?: boolean | null
  edgeAgentOnline: boolean
  dataRefreshHz: number
  latestDataTime?: string | null
  serverTime: string
}

export function getSystemHealth(experimentId?: number) {
  return request.get<ApiResponse<SystemHealthStatus>>('/api/health/system', {
    params: experimentId ? { experimentId } : undefined,
  })
}
