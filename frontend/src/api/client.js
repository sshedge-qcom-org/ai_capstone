import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
  timeout: 15000,
})

let accessToken = null
let refreshPromise = null
let onSession = () => {}

export function configureSession(callback) {
  onSession = callback
}

export function acceptSession(session) {
  accessToken = session?.access_token ?? null
  onSession(session?.user ?? null)
}

export function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = api.post('/auth/refresh')
      .then(({ data }) => { acceptSession(data); return data.user })
      .finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

api.interceptors.request.use(config => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

api.interceptors.response.use(response => response, async error => {
  const config = error.config
  if (error.response?.status === 401 && config && !config._retried && !config.url.startsWith('/auth/')) {
    config._retried = true
    try { await refreshSession() }
    catch (refreshError) { acceptSession(null); return Promise.reject(refreshError) }
    return api(config)
  }
  return Promise.reject(error)
})

export function errorMessage(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map(item => `${item.loc.at(-1)}: ${item.msg}`).join('; ')
  return typeof detail === 'string' ? detail : 'Unable to reach the service. Please try again.'
}
