import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
  timeout: 15000,
})

export function errorMessage(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map(item => `${item.loc.at(-1)}: ${item.msg}`).join('; ')
  return typeof detail === 'string' ? detail : 'Unable to reach the service. Please try again.'
}
