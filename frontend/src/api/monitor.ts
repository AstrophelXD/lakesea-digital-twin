import request, { type ApiResponse } from './request'

export interface MonitorFrame {
  experimentId: number
  shipCode: string
  timestamp: string
  position: { x: number; y: number }
  speed: number
  heading: number
  roll: number
  pitch: number
  battery: number
  resistance: number
  alarm?: {
    id: number
    type: string
    level: string
    message: string
  } | null
}

export interface MonitorStatus {
  experimentId: number
  running: boolean
  connectedClients: number
  frameCount: number
  dataSource?: 'websocket_sim' | 'mqtt'
  mqttConnected?: boolean | null
}

export interface MqttInfo {
  enabled: boolean
  connected: boolean
  brokerHost: string
  brokerPort: number
  topicPrefix: string
  subscribedTopic: string
  dataSource: 'websocket_sim' | 'mqtt'
}

export function getMqttInfo() {
  return request.get<ApiResponse<MqttInfo>>('/api/monitor/mqtt/info')
}

export function getMonitorStatus(experimentId: number) {
  return request.get<ApiResponse<MonitorStatus>>(`/api/monitor/${experimentId}/status`)
}

export function startMonitor(experimentId: number) {
  return request.post<ApiResponse<MonitorStatus>>(`/api/monitor/${experimentId}/start`)
}

export function stopMonitor(experimentId: number) {
  return request.post<ApiResponse<MonitorStatus>>(`/api/monitor/${experimentId}/stop`)
}

export function getMonitorSnapshot(experimentId: number) {
  return request.get<ApiResponse<{ latest?: MonitorFrame; tracks: { positionX?: number; positionY?: number }[] }>>(
    `/api/monitor/${experimentId}/snapshot`,
  )
}

export function triggerDemoAlarm(experimentId: number, alarmType: string) {
  return request.post<ApiResponse<MonitorFrame>>(`/api/monitor/${experimentId}/demo-alarm`, null, {
    params: { alarmType },
  })
}

export function buildMonitorWsUrl(experimentId: number, token: string) {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${proto}//${host}/ws/monitor/${experimentId}?token=${encodeURIComponent(token)}`
}
