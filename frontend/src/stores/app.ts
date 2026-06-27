import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    theme: localStorage.getItem('tawep-theme') || 'light',
    locale: localStorage.getItem('tawep-locale') || 'en'
  }),
  actions: {
    applyTheme() {
      document.documentElement.classList.toggle('dark', this.theme === 'dark')
    },
    setTheme(theme: string) {
      this.theme = theme
      localStorage.setItem('tawep-theme', theme)
      this.applyTheme()
    },
    setLocale(locale: string) {
      this.locale = locale
      localStorage.setItem('tawep-locale', locale)
    }
  }
})
