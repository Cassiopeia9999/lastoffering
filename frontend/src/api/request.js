import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 请求拦截：自动附加 Token
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一错误处理
request.interceptors.response.use(
  res => res.data,
  err => {
    const status = err.response?.status
    const detail = err.response?.data?.detail || '请求失败'
    const url = err.config?.url || ''

    if (status === 401) {
      // 登录接口的401显示具体错误，其他接口才是过期
      if (url.includes('/login')) {
        ElMessage.error(detail || '用户名或密码错误')
      } else {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      }
    } else if (status === 403) {
      ElMessage.error('权限不足')
    } else if (status === 404) {
      ElMessage.error('资源不存在')
    } else {
      ElMessage.error(detail)
    }
    return Promise.reject(err)
  }
)

export default request
