import request, { type ApiResponse } from './request'

export interface TeacherOption {
  id: number
  username: string
  realName: string
}

export interface UserItem {
  id: number
  username: string
  realName: string
  phone?: string
  email?: string
  status: string
  roles: string[]
}

export interface UserPage {
  items: UserItem[]
  total: number
  page: number
  pageSize: number
}

export function listTeachers() {
  return request.get<ApiResponse<TeacherOption[]>>('/api/users/teachers')
}

export function listUsers(params: {
  keyword?: string
  status?: string
  page?: number
  pageSize?: number
}) {
  return request.get<ApiResponse<UserPage>>('/api/users', { params })
}

export function createUser(data: {
  username: string
  password: string
  realName: string
  phone?: string
  email?: string
  roleCode: string
}) {
  return request.post<ApiResponse<UserItem>>('/api/users', data)
}

export function updateUser(
  id: number,
  data: {
    realName?: string
    phone?: string
    email?: string
    roleCode?: string
  },
) {
  return request.put<ApiResponse<UserItem>>(`/api/users/${id}`, data)
}

export function resetUserPassword(id: number, password: string) {
  return request.post<ApiResponse<null>>(`/api/users/${id}/reset-password`, { password })
}

export function toggleUserStatus(id: number) {
  return request.post<ApiResponse<UserItem>>(`/api/users/${id}/disable`)
}
