import { defineStore } from 'pinia'
import { apiGet, apiPost, getAccessToken, setAccessToken } from '../api/client'

export type AuthUser = {
  id: string
  email: string
  alias: string
  role: 'user' | 'admin'
  status: string
  preferred_locale: string
  theme: string
  email_verified_at: string | null
}

type AuthResponse = {
  access_token: string
  expires_in: number
  user: AuthUser
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as AuthUser | null,
    initialized: false,
    initializing: null as Promise<void> | null
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    isAdmin: (state) => state.user?.role === 'admin'
  },
  actions: {
    applySession(payload: AuthResponse) {
      setAccessToken(payload.access_token)
      this.user = payload.user
    },
    clearSession() {
      setAccessToken(null)
      this.user = null
    },
    async initialize() {
      if (this.initialized) return
      if (this.initializing) return this.initializing
      this.initializing = (async () => {
        try {
          if (getAccessToken()) {
            this.user = await apiGet<AuthUser>('/me')
          } else {
            this.applySession(await apiPost<AuthResponse>('/auth/refresh'))
          }
        } catch {
          this.clearSession()
        } finally {
          this.initialized = true
          this.initializing = null
        }
      })()
      return this.initializing
    },
    async login(identifier: string, password: string) {
      const payload = await apiPost<AuthResponse>('/auth/login', { identifier, password })
      this.applySession(payload)
    },
    async verifyEmail(token: string) {
      const payload = await apiPost<AuthResponse>('/auth/email/verify', { token })
      this.applySession(payload)
    },
    async logout() {
      try {
        await apiPost('/auth/logout')
      } finally {
        this.clearSession()
      }
    }
  }
})
