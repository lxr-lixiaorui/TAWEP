<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowRight, KeyRound, Mail, UserPlus } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import PublicHeader from '../components/PublicHeader.vue'
import { ApiError, apiGet, apiPost } from '../api/client'
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
const crossBorderVisible = ref(false)
const crossBorderVersion = ref<string | null>(null)
const form = reactive({
  email: '', alias: '', password: '', confirmPassword: '',
  baselineWritingScore: '' as '' | number, plannedExamDate: '',
  coreAgreementsAccepted: false, crossBorderAccepted: false, modelImprovementAccepted: false
})
const today = new Date()
const minimumExamDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const legalVersions = {
  terms: '2026-07-16', privacy: '2026-07-15', modelImprovement: '2026-07-15'
}

const copy = computed(() => app.locale === 'zh' ? {
  overline: '账户', title: '继续你的写作练习', body: '登录后，答题记录、报告和积分会保存到你的账户。',
  login: '登录', register: '注册', forgot: '忘记密码', email: '邮箱', alias: '昵称', password: '密码',
  confirm: '确认密码', loginAction: '登录', registerAction: '创建账户', forgotAction: '发送重置邮件',
  forgotLink: '忘记密码？', back: '返回登录', passwordHint: '至少 10 个字符', mismatch: '两次输入的密码不一致。',
  registered: '验证邮件已进入发送队列，请通过邮件中的链接激活账户。',
  resetQueued: '如果账户存在，密码重置邮件已进入发送队列。', resend: '重新发送验证邮件',
  securityPassword: 'Argon2 密码哈希', securityEmail: '邮箱验证',
  currentScore: '当前 TOEFL 写作分数（可选）', currentScoreHint: '0–30 分，用于之后计算真实提分。',
  examDate: '计划考试日期（可选）', examDateHint: '距离考试还有 0–7 天时，每次评分只消耗 2 credits；考试当天登录还会收到提醒。',
  acceptCorePrefix: '我已阅读并同意', acceptTerms: '《TAWEP 用户服务协议》', acceptCoreJoin: '和', acceptPrivacy: '《TAWEP 隐私政策》', acceptCoreSuffix: '，包括其中的未成年人使用规则。',
  acceptCrossBorder: '我单独同意将相关个人信息传输至香港服务器并进行存储和处理。',
  improveModel: '可选：我同意平台使用去标识化后的文章和报告改进评分模型。',
  consentRequired: '请先同意用户协议和隐私政策。', crossBorderRequired: '请先同意当前跨境处理告知。'
} : {
  overline: 'Account', title: 'Continue your writing practice', body: 'Sign in to keep sessions, reports, and credits attached to your account.',
  login: 'Sign in', register: 'Register', forgot: 'Reset password', email: 'Email', alias: 'Display name', password: 'Password',
  confirm: 'Confirm password', loginAction: 'Sign in', registerAction: 'Create account', forgotAction: 'Send reset email',
  forgotLink: 'Forgot password?', back: 'Back to sign in', passwordHint: 'At least 10 characters', mismatch: 'Passwords do not match.',
  registered: 'The verification email is queued. Use its link to activate your account.',
  resetQueued: 'If the account exists, a password reset email is queued.', resend: 'Resend verification email',
  securityPassword: 'Argon2 password hashing', securityEmail: 'Email verification',
  currentScore: 'Current TOEFL Writing score (optional)', currentScoreHint: '0–30; used later to calculate your verified improvement.',
  examDate: 'Planned exam date (optional)', examDateHint: 'When your exam is 0–7 days away, each evaluation costs only 2 credits. You will also receive an exam-day reminder.',
  acceptCorePrefix: 'I have read and agree to the', acceptTerms: 'TAWEP User Service Agreement', acceptCoreJoin: 'and', acceptPrivacy: 'TAWEP Privacy Policy', acceptCoreSuffix: ', including the rules for minors.',
  acceptCrossBorder: 'I separately consent to transmission, storage, and processing on servers in Hong Kong.',
  improveModel: 'Optional: I allow de-identified writing and reports to improve the evaluation model.',
  consentRequired: 'Agree to the user agreement and privacy policy first.', crossBorderRequired: 'Agree to the current cross-border notice first.'
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
  if (mode.value === 'register' && !form.coreAgreementsAccepted) {
    error.value = copy.value.consentRequired
    return
  }
  if (mode.value === 'register' && crossBorderVisible.value && !form.crossBorderAccepted) {
    error.value = copy.value.crossBorderRequired
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
        preferred_locale: app.locale,
        baseline_writing_score: form.baselineWritingScore === '' ? null : Number(form.baselineWritingScore),
        planned_exam_date: form.plannedExamDate || null,
        terms_accepted: true,
        terms_version: legalVersions.terms,
        privacy_accepted: true,
        privacy_version: legalVersions.privacy,
        cross_border_accepted: crossBorderVisible.value && form.crossBorderAccepted,
        cross_border_version: crossBorderVisible.value ? crossBorderVersion.value : null,
        model_improvement_accepted: form.modelImprovementAccepted,
        model_improvement_version: legalVersions.modelImprovement
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

onMounted(async () => {
  try {
    const config = await apiGet<{ visible: boolean; consent_version: string | null }>('/legal/config')
    crossBorderVisible.value = config.visible
    crossBorderVersion.value = config.consent_version
  } catch {
    crossBorderVisible.value = false
    crossBorderVersion.value = null
  }
})
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

          <div v-if="mode === 'register'" class="registration-profile-fields">
            <label class="form-field">
              <span>{{ copy.currentScore }}</span>
              <input v-model.number="form.baselineWritingScore" class="input" type="number" min="0" max="30" step="1" inputmode="numeric" />
              <small class="muted">{{ copy.currentScoreHint }}</small>
            </label>
            <label class="form-field">
              <span>{{ copy.examDate }}</span>
              <input v-model="form.plannedExamDate" class="input" type="date" :min="minimumExamDate" />
              <small class="exam-credit-hint">{{ copy.examDateHint }}</small>
            </label>
          </div>

          <fieldset v-if="mode === 'register'" class="consent-group">
            <legend>{{ app.locale === 'zh' ? '协议与选择' : 'Agreements and choices' }}</legend>
            <label class="consent-row">
              <input v-model="form.coreAgreementsAccepted" type="checkbox" required />
              <span>
                {{ copy.acceptCorePrefix }}
                <router-link to="/agreements/terms" target="_blank">{{ copy.acceptTerms }}</router-link>
                {{ copy.acceptCoreJoin }}
                <router-link to="/agreements/privacy" target="_blank">{{ copy.acceptPrivacy }}</router-link>{{ copy.acceptCoreSuffix }}
              </span>
            </label>
            <label v-if="crossBorderVisible" class="consent-row">
              <input v-model="form.crossBorderAccepted" type="checkbox" required />
              <span><router-link to="/agreements/cross-border" target="_blank">{{ copy.acceptCrossBorder }}</router-link></span>
            </label>
            <label class="consent-row optional">
              <input v-model="form.modelImprovementAccepted" type="checkbox" />
              <span><router-link to="/agreements/model-improvement" target="_blank">{{ copy.improveModel }}</router-link></span>
            </label>
          </fieldset>
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
