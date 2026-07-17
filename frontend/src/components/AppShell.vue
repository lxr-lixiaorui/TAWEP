<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { CalendarDays, Globe2, Inbox, LogOut, Moon, Settings, ShieldCheck, Sparkles, Sun } from '@lucide/vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { apiGet, apiPost } from '../api/client'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'
import PublicHeader from './PublicHeader.vue'
import SiteFooter from './SiteFooter.vue'

const props = defineProps<{ publicView?: boolean }>()

const app = useAppStore()
const auth = useAuthStore()
const router = useRouter()
const { locale, t } = useI18n()
const reminderOpen = ref(false)
const reminderSubmitting = ref(false)
const reminderError = ref('')
const examDate = ref('')
const consentOpen = ref(false)
const consentAccepted = ref(false)
const consentSubmitting = ref(false)
const consentError = ref('')
const consentVersion = ref('')
const reminderCopy = computed(() => app.locale === 'zh' ? {
  overline: '考试日祝福',
  title: `祝你今天考试顺利，${auth.user?.alias ?? ''}`,
  body: '相信你的准备，保持专注，清晰表达自己的观点。祝你发挥出色，取得理想成绩。',
  followup: '成绩公布后，可以从收件箱进入成绩登记页，记录真实提分并帮助我们继续改进 TAWEP。',
  action: '我已阅读，收下祝福',
  error: '暂时无法保存祝福，请重试。'
} : {
  overline: 'Exam-day wishes',
  title: `Good luck today, ${auth.user?.alias ?? ''}`,
  body: 'Trust your preparation, stay focused, and express your ideas clearly. We hope you perform at your best and achieve the score you are aiming for.',
  followup: 'When scores are released, use the link saved to your Inbox to report your verified improvement and help us keep improving TAWEP.',
  action: 'I have read this',
  error: 'The good-luck message could not be saved. Please try again.'
})

const consentCopy = computed(() => app.locale === 'zh' ? {
  overline: '需要你的确认', title: '个人信息跨境处理告知',
  body: '平台已启用跨境处理告知。继续使用前，请阅读告知内容并确认同意将相关信息传输至香港服务器进行存储和处理。',
  checkbox: '我已阅读并同意当前《个人信息跨境处理告知书》。',
  document: '查看完整告知', action: '确认并继续', error: '暂时无法保存同意记录，请重试。'
} : {
  overline: 'Your confirmation is required', title: 'Cross-border Processing Notice',
  body: 'The platform has activated its cross-border processing notice. Before continuing, review it and confirm the transfer, storage, and processing of relevant information on servers in Hong Kong.',
  checkbox: 'I have read and agree to the current Cross-border Processing Notice.',
  document: 'Read the complete notice', action: 'Agree and continue', error: 'The consent record could not be saved. Please try again.'
})

async function loadExamReminder() {
  try {
    const reminder = await apiGet<{ show: boolean; exam_date: string | null }>('/me/exam-reminder')
    examDate.value = reminder.exam_date ?? ''
    reminderOpen.value = reminder.show
  } catch {
    // A reminder failure must not block the rest of the authenticated application.
  }
}

onMounted(async () => {
  if (props.publicView || !auth.user) return
  try {
    const result = await apiGet<{
      cross_border: { required: boolean; consent_version: string | null }
    }>(`/me/required-consents?locale=${app.locale}`)
    if (result.cross_border.required && result.cross_border.consent_version) {
      consentVersion.value = result.cross_border.consent_version
      consentOpen.value = true
      return
    }
  } catch {
    // Consent status failures should not make the application unusable.
  }
  await loadExamReminder()
})

async function acceptCrossBorderConsent() {
  if (!consentAccepted.value) return
  consentSubmitting.value = true
  consentError.value = ''
  try {
    await apiPost('/me/consents/cross-border', { accepted: true, version: consentVersion.value })
    consentOpen.value = false
    await loadExamReminder()
  } catch {
    consentError.value = consentCopy.value.error
  } finally {
    consentSubmitting.value = false
  }
}

async function acknowledgeReminder() {
  reminderSubmitting.value = true
  reminderError.value = ''
  try {
    await apiPost('/me/exam-reminder/acknowledge', { locale: app.locale })
    reminderOpen.value = false
  } catch {
    reminderError.value = reminderCopy.value.error
  } finally {
    reminderSubmitting.value = false
  }
}

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
  <div class="page-shell app-shell-page">
    <PublicHeader v-if="publicView" />
    <header v-else class="site-header app-header">
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
    <SiteFooter />
    <n-modal v-model:show="consentOpen" :mask-closable="false" :close-on-esc="false">
      <section class="panel required-consent-dialog" role="dialog" aria-modal="true" aria-labelledby="required-consent-title">
        <div class="required-consent-icon" aria-hidden="true"><ShieldCheck :size="28" /></div>
        <p class="eyebrow">{{ consentCopy.overline }}</p>
        <h2 id="required-consent-title">{{ consentCopy.title }}</h2>
        <p>{{ consentCopy.body }}</p>
        <router-link class="required-consent-link" to="/agreements/cross-border" target="_blank">{{ consentCopy.document }}</router-link>
        <label class="consent-row required-consent-check"><input v-model="consentAccepted" type="checkbox" /><span>{{ consentCopy.checkbox }}</span></label>
        <p v-if="consentError" class="auth-message error" role="alert">{{ consentError }}</p>
        <button class="btn primary" type="button" :disabled="!consentAccepted || consentSubmitting" @click="acceptCrossBorderConsent">{{ consentCopy.action }}</button>
      </section>
    </n-modal>
    <n-modal v-model:show="reminderOpen" :mask-closable="false" :close-on-esc="false">
      <section class="panel exam-reminder-dialog" role="dialog" aria-modal="true" aria-labelledby="exam-reminder-title">
        <div class="exam-reminder-icon" aria-hidden="true"><Sparkles :size="28" /></div>
        <p class="eyebrow">{{ reminderCopy.overline }}</p>
        <h2 id="exam-reminder-title">{{ reminderCopy.title }}</h2>
        <p>{{ reminderCopy.body }}</p>
        <div v-if="examDate" class="exam-reminder-date"><CalendarDays :size="17" />{{ examDate }}</div>
        <p class="exam-reminder-followup">{{ reminderCopy.followup }}</p>
        <p v-if="reminderError" class="auth-message error" role="alert">{{ reminderError }}</p>
        <button class="btn primary" type="button" :disabled="reminderSubmitting" @click="acknowledgeReminder">
          {{ reminderCopy.action }}
        </button>
      </section>
    </n-modal>
  </div>
</template>
