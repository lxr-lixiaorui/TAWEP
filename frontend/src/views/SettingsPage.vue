<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowUpRight, History, KeyRound, LockKeyhole, Save, Server, Trash2, X } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppShell from '../components/AppShell.vue'
import { apiDelete, apiGet, apiPatch, apiPut } from '../api/client'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'

type Usage = {
  balance: number; total_planned_credit: number
  evaluation_cost: number; can_start_evaluation: boolean; personal_api_enabled: boolean
}
type CreditEntry = {
  id: string; delta: number; reason: string; session_id?: string; question_id?: string; created_at: string
}
type AIConfig = {
  enabled: boolean; provider_name: string; endpoint: string; model_name: string
  key_configured: boolean; key_hint?: string; consent_version?: string
}

const message = useMessage()
const route = useRoute()
const router = useRouter()
const { locale } = useI18n()
const app = useAppStore()
const auth = useAuthStore()
const activeTab = ref(route.query.tab === 'usage' ? 'usage' : 'profile')
const savingProfile = ref(false)
const savingApi = ref(false)
const savingConsent = ref(false)
const changingPassword = ref(false)
const deletingAccount = ref(false)
const passwordOpen = ref(false)
const deleteOpen = ref(false)
const user = reactive({ email: '', alias: '', preferred_locale: 'en', theme: 'light' })
const passwordForm = reactive({ current_password: '', new_password: '', confirm_password: '' })
const deleteForm = reactive({ current_password: '', confirm_email: '' })
const usage = ref<Usage | null>(null)
const creditHistory = ref<CreditEntry[]>([])
const dataConsent = reactive({ model_improvement: false, version: '2026-07-15' })
const ai = reactive({
  enabled: false, provider_name: 'DeepSeek', endpoint: 'https://api.deepseek.com',
  model_name: 'deepseek-reasoner', api_key: '', key_configured: false, key_hint: '', consent: false
})
const THIRD_PARTY_AI_VERSION = '2026-07-15'

const copy = computed(() => app.locale === 'zh' ? {
  title: '设置', profileTab: '个人设置', usageTab: 'Usage 与模型', personal: '个人信息', alias: '昵称',
  language: '网站语言', theme: '主题', light: '浅色', dark: '深色', system: '跟随系统', save: '保存设置',
  saved: '设置已保存', dataTitle: '数据选择', improve: '允许使用去标识化文章和报告改进评分模型',
  improveBody: '此项完全可选，可以随时撤回。撤回不会影响此前已经合法完成的处理。',
  usage: 'Credits 使用情况', balance: '剩余 credits', cost: '每次完整评分',
  credits: 'credits', apiTitle: '个人大语言模型 API',
  historyTitle: 'Credit 记录', historyBody: '每次获得、消耗或退回都会记录在这里。', historyEmpty: '暂无 credit 记录。',
  initialCredit: '新账户初始 credits', evaluationCharge: '生成完整评分报告', evaluationRefund: '评分失败退款',
  questionReward: '上传题目审核通过奖励', openReport: '查看报告',
  apiBody: '启用后，新的评分任务将使用你的 OpenAI-compatible endpoint。API Key 会在服务器端加密保存，且不会返回完整明文。',
  enabled: '使用个人 API', provider: '服务商名称', endpoint: 'API endpoint', model: '模型名称', apiKey: 'API Key',
  keyRetain: '留空将继续使用已保存的密钥', keyRequired: '首次保存时需要填写 API Key。',
  apiConsent: '我同意将文章及生成报告所需信息提供给当前页面列明的第三方 AI 服务商。',
  apiCost: '个人 API 仍消耗相同 credits，因为答题页面、报告流程、存储和服务器处理仍由 TAWEP 提供。',
  saveApi: '保存 API 设置', apiSaved: '个人 API 设置已保存', apiInvalid: '请填写 API Key 并同意第三方 AI 处理。',
  documents: '相关文件', agreements: '协议中心', creditExplanation: 'Credits 说明',
  securityTitle: '账户安全', securityBody: '更改密码将退出当前账号在所有设备上的登录。', changePassword: '更改密码',
  currentPassword: '当前密码', newPassword: '新密码', confirmPassword: '确认新密码', passwordRule: '至少 10 个字符。',
  passwordMismatch: '两次输入的新密码不一致。', passwordChanged: '密码已更改，请重新登录。', cancel: '取消',
  dangerTitle: '注销账号', dangerBody: '永久删除你的账户以及关联的答题记录、报告、credits、收件箱和个人 API 配置。此操作无法撤销。',
  deleteAccount: '永久注销账号', deleteEyebrow: '不可逆操作', deleteConfirm: '输入账户邮箱以确认',
  deletePassword: '输入当前密码', deleteMismatch: '请输入与当前账户一致的邮箱。', accountDeleted: '账号已永久注销。',
  adminDeleteBlocked: '管理员账号必须由另一名管理员在账户管理页面删除。'
} : {
  title: 'Settings', profileTab: 'Profile', usageTab: 'Usage & model', personal: 'Personal information', alias: 'Alias',
  language: 'Website language', theme: 'Theme', light: 'Light', dark: 'Dark', system: 'System', save: 'Save settings',
  saved: 'Settings saved', dataTitle: 'Data choices', improve: 'Use de-identified writing and reports to improve the evaluation model',
  improveBody: 'This is optional and can be withdrawn at any time. Withdrawal does not affect processing already lawfully completed.',
  usage: 'Credit usage', balance: 'Credits remaining', cost: 'Per full evaluation',
  credits: 'credits', apiTitle: 'Personal large-language-model API',
  historyTitle: 'Credit history', historyBody: 'Every grant, charge, and refund is recorded here.', historyEmpty: 'No credit activity yet.',
  initialCredit: 'Initial account credits', evaluationCharge: 'Full report evaluation', evaluationRefund: 'Failed evaluation refund',
  questionReward: 'Accepted question contribution', openReport: 'Open report',
  apiBody: 'When enabled, new evaluations use your OpenAI-compatible endpoint. The API key is encrypted on the server and is never returned in full.',
  enabled: 'Use personal API', provider: 'Provider name', endpoint: 'API endpoint', model: 'Model name', apiKey: 'API key',
  keyRetain: 'Leave blank to retain the saved key', keyRequired: 'An API key is required the first time you save.',
  apiConsent: 'I agree to provide my writing and report-generation data to the third-party AI provider shown on this page.',
  apiCost: 'A personal API still consumes the same credits because TAWEP provides the answer page, report pipeline, storage, and server processing.',
  saveApi: 'Save API settings', apiSaved: 'Personal API settings saved', apiInvalid: 'Enter an API key and accept third-party AI processing.',
  documents: 'Related documents', agreements: 'Agreement center', creditExplanation: 'Credit explanation',
  securityTitle: 'Account security', securityBody: 'Changing your password signs this account out on every device.', changePassword: 'Change password',
  currentPassword: 'Current password', newPassword: 'New password', confirmPassword: 'Confirm new password', passwordRule: 'Use at least 10 characters.',
  passwordMismatch: 'The new passwords do not match.', passwordChanged: 'Password changed. Sign in again.', cancel: 'Cancel',
  dangerTitle: 'Delete account', dangerBody: 'Permanently delete your account and its practice sessions, reports, credits, inbox, and personal API configuration. This cannot be undone.',
  deleteAccount: 'Delete account permanently', deleteEyebrow: 'Irreversible action', deleteConfirm: 'Type your account email to confirm',
  deletePassword: 'Enter your current password', deleteMismatch: 'Enter the email address for this account.', accountDeleted: 'Your account was permanently deleted.',
  adminDeleteBlocked: 'An administrator account must be deleted by another administrator from account management.'
})

async function saveProfile() {
  savingProfile.value = true
  try {
    const saved = await apiPatch<any>('/me', user)
    auth.user = saved
    app.setLocale(saved.preferred_locale)
    locale.value = saved.preferred_locale
    app.setTheme(saved.theme)
    message.success(copy.value.saved)
  } finally {
    savingProfile.value = false
  }
}

async function updateImprovementConsent(value: boolean) {
  savingConsent.value = true
  try {
    const result = await apiPatch<any>('/me/consents/model-improvement', { granted: value, version: dataConsent.version })
    dataConsent.model_improvement = result.model_improvement
  } catch (error) {
    dataConsent.model_improvement = !value
    message.error(error instanceof Error ? error.message : 'Unable to update consent')
  } finally {
    savingConsent.value = false
  }
}

async function saveApi() {
  if ((!ai.key_configured && !ai.api_key.trim()) || !ai.consent) {
    message.error(copy.value.apiInvalid)
    return
  }
  savingApi.value = true
  try {
    const result = await apiPut<AIConfig>('/me/ai-config', {
      enabled: ai.enabled,
      provider_name: ai.provider_name,
      endpoint: ai.endpoint,
      model_name: ai.model_name,
      api_key: ai.api_key.trim() || null,
      third_party_ai_accepted: true,
      third_party_ai_version: THIRD_PARTY_AI_VERSION
    })
    Object.assign(ai, result, { api_key: '', consent: false, key_hint: result.key_hint || '' })
    usage.value = await apiGet<Usage>('/me/usage')
    message.success(copy.value.apiSaved)
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to save API settings')
  } finally {
    savingApi.value = false
  }
}

function openPasswordDialog() {
  Object.assign(passwordForm, { current_password: '', new_password: '', confirm_password: '' })
  passwordOpen.value = true
}

async function changePassword() {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    message.error(copy.value.passwordMismatch)
    return
  }
  changingPassword.value = true
  try {
    await apiPut('/me/password', {
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    })
    passwordOpen.value = false
    auth.clearSession()
    message.success(copy.value.passwordChanged)
    await router.replace('/login')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to change password')
  } finally {
    changingPassword.value = false
  }
}

function openDeleteDialog() {
  if (auth.user?.role === 'admin') {
    message.warning(copy.value.adminDeleteBlocked)
    return
  }
  Object.assign(deleteForm, { current_password: '', confirm_email: '' })
  deleteOpen.value = true
}

async function deleteAccount() {
  if (deleteForm.confirm_email.trim().toLowerCase() !== user.email.toLowerCase()) {
    message.error(copy.value.deleteMismatch)
    return
  }
  deletingAccount.value = true
  try {
    await apiDelete('/me/account', {
      current_password: deleteForm.current_password,
      confirm_email: deleteForm.confirm_email.trim()
    })
    deleteOpen.value = false
    auth.clearSession()
    message.success(copy.value.accountDeleted)
    await router.replace('/')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to delete account')
  } finally {
    deletingAccount.value = false
  }
}

function creditReason(entry: CreditEntry) {
  const labels: Record<string, string> = {
    initial_credit: copy.value.initialCredit,
    writing_evaluation: copy.value.evaluationCharge,
    evaluation_refund: copy.value.evaluationRefund,
    question_accepted_reward: copy.value.questionReward
  }
  return labels[entry.reason] || entry.reason
}

function formatCreditDate(value: string) {
  return new Intl.DateTimeFormat(app.locale === 'zh' ? 'zh-CN' : 'en', {
    dateStyle: 'medium', timeStyle: 'short'
  }).format(new Date(value))
}

onMounted(async () => {
  const [me, usageResult, consentResult, apiResult, historyResult] = await Promise.all([
    apiGet<any>('/me'), apiGet<Usage>('/me/usage'), apiGet<any>('/me/consents'), apiGet<AIConfig>('/me/ai-config'),
    apiGet<CreditEntry[]>('/me/credits/history')
  ])
  Object.assign(user, me)
  usage.value = usageResult
  Object.assign(dataConsent, consentResult)
  Object.assign(ai, apiResult, { api_key: '', consent: false, key_hint: apiResult.key_hint || '' })
  creditHistory.value = historyResult
})
</script>

<template>
  <AppShell>
    <header class="settings-head"><p class="eyebrow">TAWEP</p><h1 class="simple-title">{{ copy.title }}</h1></header>
    <n-tabs v-model:value="activeTab" type="line" animated class="settings-tabs">
      <n-tab-pane name="profile" :tab="copy.profileTab">
        <div class="settings-grid">
          <form class="panel panel-pad settings-card" @submit.prevent="saveProfile">
            <h2>{{ copy.personal }}</h2>
            <label class="form-field"><span>{{ copy.alias }}</span><input v-model.trim="user.alias" class="input" maxlength="80" required /></label>
            <label class="form-field"><span>{{ copy.language }}</span><select v-model="user.preferred_locale" class="select"><option value="en">English</option><option value="zh">中文</option></select></label>
            <label class="form-field"><span>{{ copy.theme }}</span><select v-model="user.theme" class="select"><option value="light">{{ copy.light }}</option><option value="dark">{{ copy.dark }}</option><option value="system">{{ copy.system }}</option></select></label>
            <button class="btn primary" type="submit" :disabled="savingProfile"><Save :size="16" />{{ copy.save }}</button>
          </form>
          <section class="panel panel-pad settings-card">
            <h2>{{ copy.dataTitle }}</h2>
            <div class="settings-switch-row">
              <div><strong>{{ copy.improve }}</strong><p>{{ copy.improveBody }}</p><router-link to="/agreements/model-improvement">{{ copy.agreements }}</router-link></div>
              <n-switch :value="dataConsent.model_improvement" :loading="savingConsent" @update:value="updateImprovementConsent" />
            </div>
          </section>
          <section class="panel panel-pad settings-card account-security-card">
            <div class="account-security-copy"><h2>{{ copy.securityTitle }}</h2><p>{{ copy.securityBody }}</p></div>
            <button class="btn ghost" type="button" @click="openPasswordDialog"><KeyRound :size="16" />{{ copy.changePassword }}</button>
            <div class="account-danger-copy"><strong>{{ copy.dangerTitle }}</strong><p>{{ auth.user?.role === 'admin' ? copy.adminDeleteBlocked : copy.dangerBody }}</p></div>
            <button class="btn danger" type="button" :disabled="auth.user?.role === 'admin'" @click="openDeleteDialog"><Trash2 :size="16" />{{ copy.deleteAccount }}</button>
          </section>
        </div>
      </n-tab-pane>

      <n-tab-pane name="usage" :tab="copy.usageTab">
        <section class="usage-strip">
          <div><span>{{ copy.balance }}</span><strong>{{ usage ? usage.balance : '—' }}</strong></div>
          <div><span>{{ copy.cost }}</span><strong>{{ usage ? usage.evaluation_cost : '—' }}</strong></div>
        </section>

        <section class="panel credit-history-panel">
          <header class="credit-history-head">
            <div class="credit-history-icon"><History :size="20" /></div>
            <div><h2>{{ copy.historyTitle }}</h2><p>{{ copy.historyBody }}</p></div>
          </header>
          <div v-if="creditHistory.length" class="credit-history-list">
            <article v-for="entry in creditHistory" :key="entry.id" class="credit-history-row">
              <span class="credit-delta" :class="entry.delta > 0 ? 'gain' : 'spend'">{{ entry.delta > 0 ? '+' : '' }}{{ entry.delta }}</span>
              <div><strong>{{ creditReason(entry) }}</strong><small>{{ formatCreditDate(entry.created_at) }}</small></div>
              <router-link v-if="entry.session_id" class="credit-history-link" :to="`/${entry.session_id}/report`">
                {{ copy.openReport }}<ArrowUpRight :size="15" />
              </router-link>
            </article>
          </div>
          <p v-else class="credit-history-empty">{{ copy.historyEmpty }}</p>
        </section>

        <form class="panel api-settings" @submit.prevent="saveApi">
          <header class="api-settings-head">
            <div class="api-icon"><Server :size="22" /></div>
            <div><h2>{{ copy.apiTitle }}</h2><p>{{ copy.apiBody }}</p></div>
            <div class="api-enable"><span>{{ copy.enabled }}</span><n-switch v-model:value="ai.enabled" /></div>
          </header>
          <div class="api-settings-body">
            <div class="form-grid api-fields">
              <label class="form-field"><span>{{ copy.provider }}</span><input v-model.trim="ai.provider_name" class="input" maxlength="80" required /></label>
              <label class="form-field"><span>{{ copy.model }}</span><input v-model.trim="ai.model_name" class="input" maxlength="160" required /></label>
            </div>
            <label class="form-field"><span>{{ copy.endpoint }}</span><input v-model.trim="ai.endpoint" class="input" type="url" inputmode="url" required /></label>
            <label class="form-field"><span>{{ copy.apiKey }} <small v-if="ai.key_hint">{{ ai.key_hint }}</small></span><input v-model="ai.api_key" class="input" type="password" autocomplete="new-password" :placeholder="ai.key_configured ? copy.keyRetain : copy.keyRequired" /></label>
            <div class="api-security-note"><LockKeyhole :size="17" /><span>{{ copy.apiCost }}</span></div>
            <label class="consent-row api-consent">
              <input v-model="ai.consent" type="checkbox" />
              <span><router-link to="/agreements/third-party-ai" target="_blank">{{ copy.apiConsent }}</router-link></span>
            </label>
          </div>
          <footer class="api-settings-footer">
            <router-link to="/agreements/credit-explanation">{{ copy.creditExplanation }}</router-link>
            <button class="btn primary" type="submit" :disabled="savingApi"><KeyRound :size="16" />{{ copy.saveApi }}</button>
          </footer>
        </form>
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="passwordOpen">
      <div class="panel admin-dialog settings-dialog" role="dialog" aria-modal="true" aria-labelledby="change-password-title">
        <header><div><p class="eyebrow">{{ copy.securityTitle }}</p><h2 id="change-password-title">{{ copy.changePassword }}</h2></div><button class="btn ghost small icon-btn" type="button" :title="copy.cancel" @click="passwordOpen = false"><X :size="17" /></button></header>
        <form @submit.prevent="changePassword">
          <label class="form-field"><span>{{ copy.currentPassword }}</span><input v-model="passwordForm.current_password" class="input" type="password" autocomplete="current-password" maxlength="128" required /></label>
          <label class="form-field"><span>{{ copy.newPassword }}</span><input v-model="passwordForm.new_password" class="input" type="password" autocomplete="new-password" minlength="10" maxlength="128" required /><small>{{ copy.passwordRule }}</small></label>
          <label class="form-field"><span>{{ copy.confirmPassword }}</span><input v-model="passwordForm.confirm_password" class="input" type="password" autocomplete="new-password" minlength="10" maxlength="128" required /></label>
          <footer><button class="btn" type="button" @click="passwordOpen = false">{{ copy.cancel }}</button><button class="btn primary" type="submit" :disabled="changingPassword"><KeyRound :size="16" />{{ copy.changePassword }}</button></footer>
        </form>
      </div>
    </n-modal>

    <n-modal v-model:show="deleteOpen">
      <div class="panel admin-dialog danger-dialog settings-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-own-account-title">
        <header><div><p class="eyebrow">{{ copy.deleteEyebrow }}</p><h2 id="delete-own-account-title">{{ copy.dangerTitle }}</h2></div><button class="btn ghost small icon-btn" type="button" :title="copy.cancel" @click="deleteOpen = false"><X :size="17" /></button></header>
        <p>{{ copy.dangerBody }}</p>
        <form @submit.prevent="deleteAccount">
          <label class="form-field"><span>{{ copy.deleteConfirm }}</span><input v-model="deleteForm.confirm_email" class="input" type="email" autocomplete="off" required /></label>
          <label class="form-field"><span>{{ copy.deletePassword }}</span><input v-model="deleteForm.current_password" class="input" type="password" autocomplete="current-password" maxlength="128" required /></label>
          <footer><button class="btn" type="button" @click="deleteOpen = false">{{ copy.cancel }}</button><button class="btn danger" type="submit" :disabled="deletingAccount || deleteForm.confirm_email.trim().toLowerCase() !== user.email.toLowerCase()"><Trash2 :size="16" />{{ copy.deleteAccount }}</button></footer>
        </form>
      </div>
    </n-modal>
  </AppShell>
</template>
