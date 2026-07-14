<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { CheckCircle2, LoaderCircle, XCircle } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import PublicHeader from '../components/PublicHeader.vue'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const auth = useAuthStore()
const state = ref<'loading' | 'success' | 'error'>('loading')
const message = ref('')
const copy = computed(() => app.locale === 'zh'
  ? { loading: '正在验证邮箱', success: '邮箱验证完成', action: '进入控制台', failed: '验证链接无效或已过期', retry: '返回登录' }
  : { loading: 'Verifying your email', success: 'Email verified', action: 'Open dashboard', failed: 'The verification link is invalid or expired', retry: 'Back to sign in' })

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) {
    state.value = 'error'
    message.value = copy.value.failed
    return
  }
  try {
    await auth.verifyEmail(token)
    state.value = 'success'
  } catch (error) {
    state.value = 'error'
    message.value = app.locale === 'zh' ? copy.value.failed : error instanceof Error ? error.message : copy.value.failed
  }
})
</script>

<template>
  <div class="page-shell">
    <PublicHeader />
    <main class="container auth-result-wrap">
      <section class="panel auth-result">
        <LoaderCircle v-if="state === 'loading'" class="spin" :size="34" />
        <CheckCircle2 v-else-if="state === 'success'" class="success-icon" :size="34" />
        <XCircle v-else class="error-icon" :size="34" />
        <h1>{{ state === 'loading' ? copy.loading : state === 'success' ? copy.success : copy.failed }}</h1>
        <p v-if="message" class="muted">{{ message }}</p>
        <button v-if="state === 'success'" class="btn primary" @click="router.replace('/dashboard')">{{ copy.action }}</button>
        <button v-else-if="state === 'error'" class="btn" @click="router.replace('/login')">{{ copy.retry }}</button>
      </section>
    </main>
  </div>
</template>
