<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useAppStore } from '../stores/app'

const app = useAppStore()
const { locale } = useI18n()

function toggleTheme() {
  app.setTheme(app.theme === 'dark' ? 'light' : 'dark')
}

function toggleLocale() {
  const next = app.locale === 'en' ? 'zh' : 'en'
  app.setLocale(next)
  locale.value = next
}
</script>

<template>
  <div class="page-shell">
    <header class="site-header">
      <div class="brand-inline">
        <router-link class="brand-title" to="/">TAWEP</router-link>
        <nav class="nav-links">
          <router-link to="/dashboard">Dashboard</router-link>
          <router-link to="/questionbank">Question Bank</router-link>
          <router-link to="/examplereport">Example Report</router-link>
        </nav>
      </div>
      <div class="header-actions">
        <button class="btn ghost small" @click="toggleLocale">Language · {{ app.locale === 'en' ? 'EN' : '中文' }}</button>
        <button class="btn ghost small" @click="toggleTheme">{{ app.theme === 'dark' ? 'Light' : 'Dark' }}</button>
        <router-link class="btn ghost small" to="/inbox">Inbox</router-link>
        <router-link class="btn ghost small" to="/settings">Settings</router-link>
      </div>
    </header>
    <main class="container main-space">
      <slot />
    </main>
  </div>
</template>


