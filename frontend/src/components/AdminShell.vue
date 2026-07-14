<script setup lang="ts">
import { ArrowLeft, LogOut } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const { t } = useI18n()

async function logout() {
  await auth.logout()
  await router.push('/login')
}
</script>

<template>
  <div class="page-shell">
    <div class="admin-layout">
      <aside class="panel admin-side">
        <router-link class="brand-title" to="/manage/questionbank">TAWEP</router-link>
        <span class="admin-identity">{{ auth.user?.alias }}</span>
        <nav>
          <router-link to="/manage/questionbank">Question Bank</router-link>
          <router-link to="/manage/reviewquestion">Review Uploads</router-link>
          <router-link to="/manage/feedback">{{ t('adminFeedback.nav') }}</router-link>
          <router-link to="/manage/accounts">Accounts</router-link>
        </nav>
        <div class="admin-side-actions">
          <router-link class="btn ghost small icon-btn" to="/dashboard" title="Back to site" aria-label="Back to site"><ArrowLeft :size="16" /></router-link>
          <button class="btn ghost small icon-btn" title="Log out" aria-label="Log out" @click="logout"><LogOut :size="16" /></button>
        </div>
      </aside>
      <main class="admin-main">
        <slot />
      </main>
    </div>
  </div>
</template>
