const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'
const ACCESS_TOKEN_KEY = 'tawep-access-token'

export class ApiError extends Error {
  status: number
  code?: string

  constructor(status: number, message: string, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export function getAccessToken() {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token: string | null) {
  if (token) sessionStorage.setItem(ACCESS_TOKEN_KEY, token)
  else sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  window.dispatchEvent(new CustomEvent('tawep-auth-changed'))
}

async function responseError(response: Response) {
  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    const body = await response.json().catch(() => ({}))
    const detail = body.detail
    if (typeof detail === 'object' && detail) {
      return new ApiError(response.status, detail.message ?? 'Request failed', detail.code)
    }
    return new ApiError(response.status, typeof detail === 'string' ? detail : 'Request failed')
  }
  return new ApiError(response.status, (await response.text()) || 'Request failed')
}

let refreshPromise: Promise<boolean> | null = null

async function refreshAccessToken() {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include'
    })
    if (!response.ok) {
      setAccessToken(null)
      return false
    }
    const payload = await response.json()
    setAccessToken(payload.access_token)
    return true
  })().finally(() => {
    refreshPromise = null
  })
  return refreshPromise
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getAccessToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: 'include'
  })
  if (response.status === 401 && retry && !path.startsWith('/auth/')) {
    if (await refreshAccessToken()) return request<T>(path, init, false)
  }
  if (!response.ok) throw await responseError(response)
  if (response.status === 204) return undefined as T
  const contentType = response.headers.get('content-type') ?? ''
  return contentType.includes('application/json') ? response.json() : (response.text() as Promise<T>)
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body)
  })
}

export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PATCH',
    body: body === undefined ? undefined : JSON.stringify(body)
  })
}

export function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    body: body === undefined ? undefined : JSON.stringify(body)
  })
}

export function apiDelete<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'DELETE',
    body: body === undefined ? undefined : JSON.stringify(body)
  })
}

export async function apiDownload(path: string, filename: string) {
  return download(path, filename, true)
}

async function download(path: string, filename: string, retry: boolean): Promise<void> {
  const token = getAccessToken()
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  })
  if (response.status === 401 && retry && await refreshAccessToken()) {
    return download(path, filename, false)
  }
  if (!response.ok) throw await responseError(response)
  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
