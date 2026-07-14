<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ArrowRight, KeyRound, Mail, UserPlus } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import PublicHeader from '../components/PublicHeader.vue'
import { ApiError, apiPost } from '../api/client'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'

type Mode = 'login' | 'register' | 'forgot'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const auth = useAuthStore()
const mode = ref<Mode>('login')
const loading = ref(false)
const error = ref('')
const notice = ref('')
const canResend = ref(false)
const form = reactive({ email: '', alias: '', password: '', confirmPassword: '' })

const copy = computed(() => app.locale === 'zh' ? {
  overline: '账户', title: '继续你的写作练习', body: '登录后，答题记录、报告和积分会保存到你的账户。',
  login: '登录', register: '注册', forgot: '忘记密码', email: '邮箱', alias: '昵称', password: '密码',
  confirm: '确认密码', loginAction: '登录', registerAction: '创建账户', forgotAction: '发送重置邮件',
  forgotLink: '忘记密码？', back: '返回登录', passwordHint: '至少 10 个字符', mismatch: '两次输入的密码不一致。',
  registered: '验证邮件已进入发送队列，请通过邮件中的链接激活账户。',
  resetQueued: '如果账户存在，密码重置邮件已进入发送队列。', resend: '重新发送验证邮件',
  securityPassword: 'Argon2 密码哈希', securityEmail: '邮箱验证'
} : {
  overline: 'Account', title: 'Continue your writing practice', body: 'Sign in to keep sessions, reports, and credits attached to your account.',
  login: 'Sign in', register: 'Register', forgot: 'Reset password', email: 'Email', alias: 'Display name', password: 'Password',
  confirm: 'Confirm password', loginAction: 'Sign in', registerAction: 'Create account', forgotAction: 'Send reset email',
  forgotLink: 'Forgot password?', back: 'Back to sign in', passwordHint: 'At least 10 characters', mismatch: 'Passwords do not match.',
  registered: 'The verification email is queued. Use its link to activate your account.',
  resetQueued: 'If the account exists, a password reset email is queued.', resend: 'Resend verification email',
  securityPassword: 'Argon2 password hashing', securityEmail: 'Email verification'
})

function selectMode(next: Mode) {
  mode.value = next
  error.value = ''
  notice.value = ''
  canResend.value = false
}

function errorMessage(value: unknown) {
  if (app.locale === 'zh' && value instanceof ApiError) {
    const translated: Record<string, string> = {
      INVALID_CREDENTIALS: '邮箱或密码不正确。',
      EMAIL_NOT_VERIFIED: '请先通过验证邮件激活账户。',
      ACCOUNT_DISABLED: '当前账户不可用。',
      INVALID_TOKEN: '链接无效或已过期。'
    }
    if (value.code && translated[value.code]) return translated[value.code]
  }
  return value instanceof Error ? value.message : 'Request failed. Please try again.'
}

async function submit() {
  error.value = ''
  notice.value = ''
  canResend.value = false
  if (mode.value === 'register' && form.password !== form.confirmPassword) {
    error.value = copy.value.mismatch
    return
  }
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(form.email, form.password)
      const redirect = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
        ? route.query.redirect
        : '/dashboard'
      await router.replace(redirect)
    } else if (mode.value === 'register') {
      await apiPost('/auth/register', {
        email: form.email,
        alias: form.alias,
        password: form.password,
        preferred_locale: app.locale
      })
      notice.value = copy.value.registered
    } else {
      await apiPost('/auth/password/forgot', { email: form.email, preferred_locale: app.locale })
      notice.value = copy.value.resetQueued
    }
  } catch (value) {
    error.value = errorMessage(value)
    canResend.value = value instanceof ApiError && value.code === 'EMAIL_NOT_VERIFIED'
  } finally {
    loading.value = false
  }
}

async function resendVerification() {
  loading.value = true
  error.value = ''
  try {
    await apiPost('/auth/email/resend', { email: form.email, preferred_locale: app.locale })
    notice.value = copy.value.registered
    canResend.value = false
  } catch (value) {
    error.value = errorMessage(value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page-shell">
    <PublicHeader />
    <main class="container auth-page">
      <section class="auth-intro">
        <p class="eyebrow">{{ copy.overline }}</p>
        <h1>{{ copy.title }}</h1>
        <p>{{ copy.body }}</p>
        <div class="auth-assurance">
          <span><KeyRound :size="17" />{{ copy.securityPassword }}</span>
          <span><Mail :size="17" />{{ copy.securityEmail }}</span>
        </div>
      </section>

      <section class="auth-panel panel">
        <div v-if="mode !== 'forgot'" class="auth-switch" role="tablist">
          <button type="button" :class="{ active: mode === 'login' }" @click="selectMode('login')">{{ copy.login }}</button>
          <button type="button" :class="{ active: mode === 'register' }" @click="selectMode('register')">{{ copy.register }}</button>
        </div>
        <button v-else type="button" class="auth-back" @click="selectMode('login')">{{ copy.back }}</button>

        <form @submit.prevent="submit">
          <h2>{{ mode === 'login' ? copy.login : mode === 'register' ? copy.register : copy.forgot }}</h2>
          <label class="form-field">
            <span>{{ copy.email }}</span>
            <input v-model="form.email" class="input" type="email" autocomplete="email" required />
          </label>
          <label v-if="mode === 'register'" class="form-field">
            <span>{{ copy.alias }}</span>
            <input v-model="form.alias" class="input" autocomplete="nickname" maxlength="80" required />
          </label>
          <label v-if="mode !== 'forgot'" class="form-field">
            <span>{{ copy.password }}</span>
            <input v-model="form.password" class="input" type="password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" :minlength="mode === 'register' ? 10 : 1" required />
            <small v-if="mode === 'register'" class="muted">{{ copy.passwordHint }}</small>
          </label>
          <label v-if="mode === 'register'" class="form-field">
            <span>{{ copy.confirm }}</span>
            <input v-model="form.confirmPassword" class="input" type="password" autocomplete="new-password" minlength="10" required />
          </label>

          <p v-if="error" class="auth-message error" role="alert">{{ error }}</p>
          <p v-if="notice" class="auth-message success" role="status">{{ notice }}</p>

          <button class="btn primary auth-submit" type="submit" :disabled="loading">
            <UserPlus v-if="mode === 'register'" :size="17" />
            <Mail v-else-if="mode === 'forgot'" :size="17" />
            <ArrowRight v-else :size="17" />
            {{ mode === 'login' ? copy.loginAction : mode === 'register' ? copy.registerAction : copy.forgotAction }}
          </button>
          <button v-if="canResend" class="btn auth-submit" type="button" :disabled="loading" @click="resendVerification">{{ copy.resend }}</button>
          <button v-if="mode === 'login'" class="auth-forgot" type="button" @click="selectMode('forgot')">{{ copy.forgotLink }}</button>
        </form>
      </section>
    </main>
  </div>
</template>
