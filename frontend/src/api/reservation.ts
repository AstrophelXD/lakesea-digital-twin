import request, { type ApiResponse } from './request'

export interface ReservationResource {
  id?: number
  resourceId: number
  resourceType?: string
  resourceName?: string
  quantity: number
  startTime: string
  endTime: string
  remark?: string
}

export interface Reservation {
  id: number
  reservationNo: string
  expName: string
  expType?: string
  applicantId: number
  applicantName?: string
  teacherId?: number
  teacherName?: string
  startTime: string
  endTime: string
  status: string
  purpose?: string
  planSummary?: string
  rejectReason?: string
  createTime?: string
  submitTime?: string
  resources?: ReservationResource[]
  approvalLogs?: ApprovalLog[]
  experimentTaskId?: number
}

export interface ConflictItem {
  resourceId: number
  resourceName?: string
  conflictReservationNo: string
  conflictExpName: string
  startTime: string
  endTime: string
}

export interface ApprovalLog {
  id: number
  stepType: string
  approverName?: string
  result: string
  comment?: string
  actionTime: string
}

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export function listReservations(params?: Record<string, unknown>) {
  return request.get<ApiResponse<PageData<Reservation>>>('/api/reservations', { params })
}

export function getReservation(id: number) {
  return request.get<ApiResponse<Reservation>>(`/api/reservations/${id}`)
}

export function createReservation(data: Record<string, unknown>) {
  return request.post<ApiResponse<Reservation>>('/api/reservations', data)
}

export function updateReservation(id: number, data: Record<string, unknown>) {
  return request.put<ApiResponse<Reservation>>(`/api/reservations/${id}`, data)
}

export function checkConflicts(id: number) {
  return request.post<ApiResponse<{ hasConflict: boolean; conflicts: ConflictItem[] }>>(
    `/api/reservations/${id}/check-conflicts`,
  )
}

export function submitReservation(id: number) {
  return request.post<ApiResponse<Reservation>>(`/api/reservations/${id}/submit`)
}

export function teacherReview(id: number, approved: boolean, comment?: string) {
  return request.post<ApiResponse<Reservation>>(`/api/reservations/${id}/teacher-review`, {
    approved,
    comment,
  })
}

export function directorApprove(id: number, approved: boolean, comment?: string) {
  return request.post<ApiResponse<Reservation>>(`/api/reservations/${id}/director-approve`, {
    approved,
    comment,
  })
}

export function cancelReservation(id: number) {
  return request.post<ApiResponse<Reservation>>(`/api/reservations/${id}/cancel`)
}
