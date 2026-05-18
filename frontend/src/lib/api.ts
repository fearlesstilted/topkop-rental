import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

export const API_TIMEOUT_MS = 90000

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: API_TIMEOUT_MS
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

type FastApiValidationError = {
  msg?: string
}

type FastApiErrorBody = {
  detail?: string | FastApiValidationError[]
}

export function errMsg(error: unknown, fallback = 'Błąd'): string {
  const detail = axios.isAxiosError(error)
    ? (error.response?.data as FastApiErrorBody | undefined)?.detail
    : undefined

  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg ?? JSON.stringify(item)).join('; ')
  }
  return fallback
}

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
    }
    return Promise.reject(err)
  }
)
