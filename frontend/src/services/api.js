const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function errorMessage(payload) {
  const detail = payload?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join(' ')
  }
  return 'The API did not respond successfully.'
}

async function request(path, options = {}) {
  const headers = {
    Accept: 'application/json',
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(errorMessage(payload))
  }
  return payload
}

export function getHealth() {
  return request('/api/v1/health')
}

export function getDashboardSummary() {
  return request('/api/v1/dashboard/summary')
}

export function getEnergyHistory(limit = 168) {
  return request(`/api/v1/energy/history?limit=${limit}`)
}

export function getRecentForecasts(limit = 8) {
  return request(`/api/v1/forecasts/recent?limit=${limit}`)
}

export function getLatestForecast() {
  return request('/api/v1/forecast/latest')
}

export function createForecast() {
  return request('/api/v1/forecast', { method: 'POST' })
}

export function getAnomalies({ severity, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  if (severity) {
    params.set('severity', severity)
  }
  return request(`/api/v1/anomalies?${params.toString()}`)
}

export function getAnomaly(id) {
  return request(`/api/v1/anomalies/${encodeURIComponent(id)}`)
}

export function getAnalytics() {
  return request('/api/v1/analytics')
}

export function getModelMetrics() {
  return request('/api/v1/model/metrics')
}

export function getWeather() {
  return request('/api/v1/weather')
}

export function submitContact(body) {
  return request('/api/v1/contact', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
