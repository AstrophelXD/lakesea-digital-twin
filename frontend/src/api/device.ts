import request, { type ApiResponse } from './request'

export interface DeviceStatusEvent {
  deviceId: string
  status: string
  commandType?: string
  executedAt?: string
  receivedAt?: string
}

export interface DeviceInfo {
  deviceId: string
  deviceName: string
  deviceType: string
  status: string
  online: boolean
  lastCommandType?: string | null
  lastAckAt?: string | null
  ackStatus?: string | null
}

export interface DeviceCommand {
  id: number
  deviceId: string
  experimentId?: number | null
  commandType: string
  commandPayload?: string | null
  issuedBy?: number | null
  issuedAt: string
  status: string
  resultMessage?: string | null
}

export function listDevices(experimentId?: number) {
  return request.get<ApiResponse<DeviceInfo[]>>('/api/devices', {
    params: experimentId ? { experimentId } : undefined,
  })
}

export function issueDeviceCommand(
  deviceId: string,
  commandType: string,
  payload?: Record<string, unknown>,
  experimentId?: number,
) {
  return request.post<ApiResponse<DeviceCommand>>(`/api/devices/${deviceId}/commands`, {
    commandType,
    payload,
  }, {
    params: experimentId ? { experimentId } : undefined,
  })
}

export function emergencyStopDevice(deviceId: string, experimentId?: number) {
  return request.post<ApiResponse<DeviceCommand>>(
    `/api/devices/${deviceId}/emergency-stop`,
    null,
    { params: experimentId ? { experimentId } : undefined },
  )
}

export function listDeviceCommands(deviceId: string, experimentId?: number) {
  return request.get<ApiResponse<{ items: DeviceCommand[]; total: number }>>(
    `/api/devices/${deviceId}/commands`,
    { params: experimentId ? { experimentId } : undefined },
  )
}
