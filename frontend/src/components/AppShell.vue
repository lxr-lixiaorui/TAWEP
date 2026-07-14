<script setup lang="ts">
import { Globe2, Inbox, LogOut, Moon, Settings, Sun } from '@lucide/vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'

const app = useAppStore()
const auth = useAuthStore()
const router = useRouter()
const { locale, t } = useI18n()

function toggleTheme() {
  app.setTheme(app.theme === 'dark' ? 'light' : 'dark')
}

function toggleLocale() {
  const next = app.locale === 'en' ? 'zh' : 'en'
  app.setLocale(next)
  locale.value = next
}

async function logout() {
  await auth.logout()
  await router.push('/')
}
</script>

<template>
  <div class="page-shell">
    <header class="site-header app-header">
      <div class="brand-inline">
        <router-link class="brand-title" to="/">TAWEP</router-link>
        <nav class="nav-links">
          <router-link to="/dashboard">{{ t('nav.dashboard') }}</router-link>
          <router-link to="/questionbank">{{ t('nav.bank') }}</router-link>
          <router-link to="/examplereport">{{ t('nav.example') }}</router-link>
        </nav>
      </div>
      <div class="header-actions">
        <span v-if="auth.user" class="header-user">{{ auth.user.alias }}</span>
        <button class="btn ghost small header-language" :title="app.locale === 'en' ? '切换到中文' : 'Switch to English'" @click="toggleLocale">
          <Globe2 :size="15" />{{ app.locale === 'en' ? '中文' : 'EN' }}
        </button>
        <button class="btn ghost small icon-btn header-icon" :title="app.theme === 'dark' ? 'Light theme' : 'Dark theme'" :aria-label="app.theme === 'dark' ? 'Light theme' : 'Dark theme'" @click="toggleTheme">
          <Sun v-if="app.theme === 'dark'" :size="17" />
          <Moon v-else :size="17" />
        </button>
        <router-link class="btn ghost small icon-btn header-icon" to="/inbox" :title="t('nav.inbox')" :aria-label="t('nav.inbox')"><Inbox :size="17" /></router-link>
        <router-link class="btn ghost small icon-btn header-icon" to="/settings" :title="t('nav.settings')" :aria-label="t('nav.settings')"><Settings :size="17" /></router-link>
        <button class="btn ghost small icon-btn header-icon" title="Log out" aria-label="Log out" @click="logout"><LogOut :size="17" /></button>
      </div>
    </header>
    <main class="container main-space">
      <slot />
    </main>
  </div>
</template>
