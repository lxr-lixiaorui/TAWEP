<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Eye, MessageSquare, Search, X } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import AdminShell from '../../components/AdminShell.vue'
import { apiGet } from '../../api/client'

type FeedbackType = 'too_high' | 'too_low' | 'other'
type FeedbackRow = {
  id: string
  session_id: string
  question_no: number
  user_id: string
  user_alias: string
  user_email: string
  feedback_type: FeedbackType
  comment: string | null
  consent_to_share: boolean
  answer_snapshot: string
  report_snapshot: Record<string, any>
  total_score: number
  created_at: string
}

const { t } = useI18n()
const message = useMessage()
const rows = ref<FeedbackRow[]>([])
const loading = ref(true)
const search = ref('')
const typeFilter = ref<'all' | FeedbackType>('all')
const selected = ref<FeedbackRow | null>(null)
const criteriaKeys = ['content_relevance', 'perspective_expansion', 'linguistic_expression', 'logical_structure'] as const

const filteredRows = computed(() => {
  const term = search.value.trim().toLowerCase()
  return rows.value.filter((row) => {
    if (typeFilter.value !== 'all' && row.feedback_type !== typeFilter.value) return false
    return !term || `${row.user_alias} ${row.user_email} ${row.question_no} ${row.comment ?? ''}`.toLowerCase().includes(term)
  })
})

function typeLabel(type: FeedbackType) {
  return t(`adminFeedback.types.${type}`)
}

function criterionLabel(key: string) {
  return t(`report.criteria.${key}`)
}

async function loadFeedback() {
  loading.value = true
  try {
    rows.value = await apiGet<FeedbackRow[]>('/admin/feedback')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to load feedback')
  } finally {
    loading.value = false
  }
}

onMounted(loadFeedback)
</script>

<template>
  <AdminShell>
    <header class="admin-page-head">
      <div><p class="eyebrow">{{ t('adminFeedback.eyebrow') }}</p><h1>{{ t('adminFeedback.title') }}</h1><p>{{ t('adminFeedback.subtitle') }}</p></div>
    </header>

    <section class="admin-account-tools question-bank-tools">
      <label class="admin-search"><Search :size="16" /><input v-model="search" :placeholder="t('adminFeedback.search')" /></label>
      <div class="admin-filter-group">
        <select v-model="typeFilter" class="select">
          <option value="all">{{ t('adminFeedback.allTypes') }}</option>
          <option value="too_high">{{ t('adminFeedback.types.too_high') }}</option>
          <option value="too_low">{{ t('adminFeedback.types.too_low') }}</option>
          <option value="other">{{ t('adminFeedback.types.other') }}</option>
        </select>
        <span>{{ t('adminFeedback.count', { count: filteredRows.length }) }}</span>
      </div>
    </section>

    <section class="panel admin-account-table-wrap">
      <table class="data-table admin-feedback-table">
        <thead><tr><th>{{ t('adminFeedback.user') }}</th><th>{{ t('adminFeedback.type') }}</th><th>{{ t('adminFeedback.report') }}</th><th>{{ t('adminFeedback.message') }}</th><th>{{ t('adminFeedback.submitted') }}</th><th aria-label="Action"></th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="muted">{{ t('adminFeedback.loading') }}</td></tr>
          <tr v-else-if="!filteredRows.length"><td colspan="6" class="admin-empty-row"><MessageSquare :size="18" />{{ t('adminFeedback.empty') }}</td></tr>
          <tr v-for="row in filteredRows" :key="row.id">
            <td><strong>{{ row.user_alias }}</strong><small class="table-secondary">{{ row.user_email }}</small></td>
            <td><span class="feedback-type-badge" :class="row.feedback_type">{{ typeLabel(row.feedback_type) }}</span></td>
            <td><strong>{{ t('adminFeedback.question', { number: row.question_no }) }}</strong><small class="table-secondary">{{ row.total_score }} / 5</small></td>
            <td class="feedback-comment-cell">{{ row.comment || t('adminFeedback.noComment') }}</td>
            <td>{{ new Date(row.created_at).toLocaleString() }}</td>
            <td><button class="btn ghost small" @click="selected = row"><Eye :size="15" />{{ t('adminFeedback.view') }}</button></td>
          </tr>
        </tbody>
      </table>
    </section>

    <n-modal :show="Boolean(selected)" @update:show="(show: boolean) => { if (!show) selected = null }">
      <div v-if="selected" class="panel admin-dialog admin-feedback-dialog" role="dialog" aria-modal="true" aria-labelledby="feedback-detail-title">
        <header><div><p class="eyebrow">{{ typeLabel(selected.feedback_type) }}</p><h2 id="feedback-detail-title">{{ t('adminFeedback.question', { number: selected.question_no }) }}</h2></div><button class="btn ghost small icon-btn" :title="t('adminFeedback.close')" :aria-label="t('adminFeedback.close')" @click="selected = null"><X :size="17" /></button></header>
        <div class="feedback-detail-meta">
          <span><small>{{ t('adminFeedback.user') }}</small><strong>{{ selected.user_alias }}</strong><em>{{ selected.user_email }}</em></span>
          <span><small>{{ t('adminFeedback.totalScore') }}</small><strong>{{ selected.total_score }} / 5</strong><em>{{ selected.report_snapshot.total_score_30 }} / 30</em></span>
          <span><small>{{ t('adminFeedback.submitted') }}</small><strong>{{ new Date(selected.created_at).toLocaleDateString() }}</strong><em>{{ new Date(selected.created_at).toLocaleTimeString() }}</em></span>
        </div>

        <section class="feedback-detail-section prominent"><h3>{{ t('adminFeedback.message') }}</h3><p>{{ selected.comment || t('adminFeedback.noComment') }}</p></section>
        <section class="feedback-detail-section"><h3>{{ t('adminFeedback.originalAnswer') }}</h3><p class="feedback-long-text">{{ selected.answer_snapshot }}</p></section>
        <section class="feedback-detail-section"><h3>{{ t('adminFeedback.criteria') }}</h3>
          <div class="feedback-criteria-list">
            <article v-for="key in criteriaKeys" :key="key">
              <header><strong>{{ criterionLabel(key) }}</strong><span>{{ selected.report_snapshot.components?.[key] }} / 5</span></header>
              <div><small>{{ t('adminFeedback.problem') }}</small><p>{{ selected.report_snapshot.problems?.[key] }}</p></div>
              <div><small>{{ t('adminFeedback.improvement') }}</small><p>{{ selected.report_snapshot.improvements?.[key] }}</p></div>
            </article>
          </div>
        </section>
        <section class="feedback-detail-section"><h3>{{ t('adminFeedback.rewrite') }}</h3><p class="feedback-long-text">{{ selected.report_snapshot.ai_rewrite }}</p></section>
        <footer><button class="btn" @click="selected = null">{{ t('adminFeedback.close') }}</button></footer>
      </div>
    </n-modal>
  </AdminShell>
</template>
