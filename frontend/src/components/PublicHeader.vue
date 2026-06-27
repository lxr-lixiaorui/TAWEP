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
  <header class="site-header">
    <router-link class="brand-block" to="/">
      <span class="brand-title">TAWEP</span>
      <span class="brand-subtitle">TOEFL Academic Writing Evaluation Project</span>
    </router-link>
    <nav class="nav-links">
      <router-link to="/questionbank">Question Bank</router-link>
      <router-link to="/examplereport">Example Report</router-link>
      <router-link to="/dashboard">Dashboard</router-link>
      <button class="btn ghost small" @click="toggleLocale">{{ app.locale === 'en' ? '中文' : 'EN' }}</button>
      <button class="btn ghost small" @click="toggleTheme">{{ app.theme === 'dark' ? 'Light' : 'Dark' }}</button>
      <router-link to="/login" class="btn">Log in</router-link>
    </nav>
  </header>
</template>
