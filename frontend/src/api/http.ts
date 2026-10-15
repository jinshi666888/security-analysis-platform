import axios, { type AxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 120000 })

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) config.headers.Authorization = `Bearer ${auth.token}`
  return config
})

http.interceptors.response.use(
  (r) => r.data,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
      location.href = '/login'
    }
    ElMessage.error(err.response?.data?.detail || '请求失败')
    return Promise.reject(err)
  }
)

// 响应拦截器已把 AxiosResponse 解包为 r.data，这里将返回类型对齐为载荷本身，
// 使各视图可直接使用 res.items / res.markdown 等字段（同时通过 vue-tsc 类型检查）。
type ApiClient = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
}

export default http as unknown as ApiClient
