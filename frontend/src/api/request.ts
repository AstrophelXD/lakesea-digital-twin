import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
})

request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse
    if (body.code !== 200) {
      ElMessage.error(body.message || '请求失败')
      if (body.code === 401) {
        localStorage.removeItem('token')
        router.push({ name: 'login' })
      }
      return Promise.reject(new Error(body.message))
    }
    return response
  },
  (error: AxiosError<ApiResponse>) => {
    const message =
      error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(message)
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      router.push({ name: 'login' })
    }
    return Promise.reject(error)
  },
)

export default request
