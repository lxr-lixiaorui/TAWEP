<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { KeyRound } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import PublicHeader from '../components/PublicHeader.vue'
import { apiPost } from '../api/client'
import { useAppStore } from '../stores/app'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const form = reactive({ password: '', confirm: '' })
const loading = ref(false)
const error = ref('')
const complete = ref(false)
const copy = computed(() => app.locale === 'zh'
  ? { title: '设置新密码', body: '新密码至少需要 10 个字符。', password: '新密码', confirm: '确认新密码', action: '更新密码', mismatch: '两次输入的密码不一致。', missing: '缺少密码重置令牌。', failed: '链接无效或已过期。', done: '密码已更新，请重新登录。', login: '返回登录' }
  : { title: 'Set a new password', body: 'Use at least 10 characters for the new password.', password: 'New password', confirm: 'Confirm new password', action: 'Update password', mismatch: 'Passwords do not match.', missing: 'Reset token is missing.', failed: 'The reset link is invalid or expired.', done: 'Password updated. Sign in again.', login: 'Back to sign in' })

async function submit() {
  error.value = ''
  if (form.password !== form.confirm) {
    error.value = copy.value.mismatch
    return
  }
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) {
    error.value = copy.value.missing
    return
  }
  loading.value = true
  try {
    await apiPost('/auth/password/reset', { token, password: form.password })
    complete.value = true
  } catch (value) {
    error.value = app.locale === 'zh' ? copy.value.failed : value instanceof Error ? value.message : copy.value.failed
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-shell">
    <PublicHeader />
    <main class="container auth-result-wrap">
      <section class="panel auth-reset-panel">
        <KeyRound :size="30" />
        <h1>{{ copy.title }}</h1>
        <p class="muted">{{ complete ? copy.done : copy.body }}</p>
        <form v-if="!complete" @submit.prevent="submit">
          <label class="form-field"><span>{{ copy.password }}</span><input v-model="form.password" class="input" type="password" autocomplete="new-password" minlength="10" required /></label>
          <label class="form-field"><span>{{ copy.confirm }}</span><input v-model="form.confirm" class="input" type="password" autocomplete="new-password" minlength="10" required /></label>
          <p v-if="error" class="auth-message error" role="alert">{{ error }}</p>
          <button class="btn primary auth-submit" type="submit" :disabled="loading">{{ copy.action }}</button>
        </form>
        <button v-else class="btn primary" @click="router.replace('/login')">{{ copy.login }}</button>
      </section>
    </main>
  </div>
</template>
