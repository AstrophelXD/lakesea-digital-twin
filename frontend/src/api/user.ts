import request, { type ApiResponse } from './request'

export interface TeacherOption {
  id: number
  username: string
  realName: string
}

export function listTeachers() {
  return request.get<ApiResponse<TeacherOption[]>>('/api/users/teachers')
}
