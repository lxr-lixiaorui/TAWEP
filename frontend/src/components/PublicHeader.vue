<script setup lang="ts">
import { Globe2, LogIn, LogOut, Moon, Sun, UserRound } from '@lucide/vue'
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
  <header class="site-header public-header">
    <router-link class="brand-block" to="/">
      <span class="brand-title">TAWEP</span>
      <span class="brand-subtitle">TOEFL Academic Writing Evaluation Project</span>
    </router-link>
    <div class="public-header-nav">
      <nav class="nav-links">
        <router-link to="/questionbank">{{ t('nav.bank') }}</router-link>
        <router-link to="/examplereport">{{ t('nav.example') }}</router-link>
        <router-link v-if="auth.isAuthenticated" to="/dashboard">{{ t('nav.dashboard') }}</router-link>
      </nav>
      <div class="header-actions">
        <button class="btn ghost small header-language" :title="app.locale === 'en' ? '切换到中文' : 'Switch to English'" @click="toggleLocale">
          <Globe2 :size="15" />{{ app.locale === 'en' ? '中文' : 'EN' }}
        </button>
        <button class="btn ghost small icon-btn header-icon" :title="app.theme === 'dark' ? 'Light theme' : 'Dark theme'" :aria-label="app.theme === 'dark' ? 'Light theme' : 'Dark theme'" @click="toggleTheme">
          <Sun v-if="app.theme === 'dark'" :size="17" />
          <Moon v-else :size="17" />
        </button>
        <template v-if="auth.isAuthenticated">
          <router-link to="/dashboard" class="btn header-login"><UserRound :size="16" />{{ auth.user?.alias }}</router-link>
          <button class="btn ghost small icon-btn header-icon" title="Log out" aria-label="Log out" @click="logout"><LogOut :size="17" /></button>
        </template>
        <router-link v-else to="/login" class="btn header-login"><LogIn :size="16" />{{ t('nav.login') }}</router-link>
      </div>
    </div>
  </header>
</template>
