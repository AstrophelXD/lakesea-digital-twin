import request, { type ApiResponse } from './request'

export interface Resource {
  id: number
  resourceCode: string
  resourceName: string
  resourceType: string
  status: string
  location?: string
  description?: string
}

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export function listResources(params?: Record<string, unknown>) {
  return request.get<ApiResponse<PageData<Resource>>>('/api/resources', { params })
}

export function createResource(data: Partial<Resource>) {
  return request.post<ApiResponse<Resource>>('/api/resources', data)
}

export function updateResource(id: number, data: Partial<Resource>) {
  return request.put<ApiResponse<Resource>>(`/api/resources/${id}`, data)
}

export function updateResourceStatus(id: number, status: string, comment?: string) {
  return request.put<ApiResponse<Resource>>(`/api/resources/${id}/status`, { status, comment })
}

export function deleteResource(id: number) {
  return request.delete<ApiResponse<null>>(`/api/resources/${id}`)
}
