import request, { type ApiResponse } from './request'

export interface UserInfo {
  id: number
  username: string
  realName: string
  phone?: string
  email?: string
  roles: string[]
}

export interface LoginResult {
  token: string
  user: UserInfo
}

export interface ProfileResult {
  user: UserInfo
  menus: string[]
}

export function login(username: string, password: string) {
  return request.post<ApiResponse<LoginResult>>('/api/auth/login', {
    username,
    password,
  })
}

export function getProfile() {
  return request.get<ApiResponse<ProfileResult>>('/api/auth/profile')
}

export function logout() {
  return request.post<ApiResponse<null>>('/api/auth/logout')
}
