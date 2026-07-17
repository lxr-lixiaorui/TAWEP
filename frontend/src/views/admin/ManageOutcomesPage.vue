<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Search, TrendingUp } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import AdminShell from '../../components/AdminShell.vue'
import { apiGet } from '../../api/client'

type OutcomeRow = {
  id: string
  user_id: string
  user_alias: string
  user_email: string
  baseline_writing_score: number | null
  writing_score: number
  improvement: number | null
  exam_date: string
  submitted_at: string
}

const message = useMessage()
const rows = ref<OutcomeRow[]>([])
const loading = ref(true)
const search = ref('')

const filteredRows = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return rows.value
  return rows.value.filter((row) => `${row.user_alias} ${row.user_email} ${row.exam_date}`.toLowerCase().includes(query))
})

const measuredRows = computed(() => rows.value.filter((row) => row.improvement !== null))
const averageImprovement = computed(() => {
  if (!measuredRows.value.length) return null
  return measuredRows.value.reduce((total, row) => total + Number(row.improvement), 0) / measuredRows.value.length
})

function signed(value: number | null) {
  if (value === null) return '—'
  return `${value > 0 ? '+' : ''}${value}`
}

async function loadOutcomes() {
  loading.value = true
  try {
    rows.value = await apiGet<OutcomeRow[]>('/admin/exam-results')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to load reported improvements')
  } finally {
    loading.value = false
  }
}

onMounted(loadOutcomes)
</script>

<template>
  <AdminShell>
    <header class="admin-page-head">
      <div><p class="eyebrow">Verified outcomes</p><h1>Reported Improvement</h1><p>User-reported TOEFL Writing outcomes retained for future aggregate analysis.</p></div>
    </header>

    <section class="admin-outcome-summary">
      <article class="panel"><span>Reports</span><strong>{{ rows.length }}</strong><small>submitted outcomes</small></article>
      <article class="panel"><span>Measured improvement</span><strong>{{ measuredRows.length }}</strong><small>with a baseline score</small></article>
      <article class="panel accent"><span>Average improvement</span><strong>{{ averageImprovement === null ? '—' : signed(Number(averageImprovement.toFixed(1))) }}</strong><small>Writing score points</small></article>
    </section>

    <section class="admin-account-tools">
      <label class="admin-search"><Search :size="16" /><input v-model="search" placeholder="Search user, email, or exam date" /></label>
      <span>{{ filteredRows.length }} records</span>
    </section>

    <section class="panel admin-account-table-wrap">
      <table class="data-table admin-outcome-table">
        <thead><tr><th>User</th><th>Before</th><th>Official</th><th>Improvement</th><th>Exam date</th><th>Submitted</th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="muted">Loading reported outcomes...</td></tr>
          <tr v-else-if="!filteredRows.length"><td colspan="6" class="admin-empty-row"><TrendingUp :size="18" />No score reports yet.</td></tr>
          <tr v-for="row in filteredRows" :key="row.id" class="outcome-row">
            <td data-label="User"><strong>{{ row.user_alias }}</strong><small class="table-secondary">{{ row.user_email }}</small></td>
            <td data-label="Before" class="score-cell">{{ row.baseline_writing_score ?? '—' }}<small v-if="row.baseline_writing_score !== null">/30</small></td>
            <td data-label="Official" class="score-cell"><strong>{{ row.writing_score }}</strong><small>/30</small></td>
            <td data-label="Improvement"><span class="outcome-delta" :class="{ positive: (row.improvement ?? 0) > 0, negative: (row.improvement ?? 0) < 0 }">{{ signed(row.improvement) }}</span></td>
            <td data-label="Exam date">{{ new Date(`${row.exam_date}T00:00:00`).toLocaleDateString() }}</td>
            <td data-label="Submitted">{{ new Date(row.submitted_at).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </AdminShell>
</template>
