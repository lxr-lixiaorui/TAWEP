<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { apiGet } from '../api/client'

type Summary = {
  alias: string
  user_id: string
  average_score: number
  practice_count: number
  credit: { balance: number; weekly_limit: number; weekly_used: number; total_planned_credit: number }
}

type MatrixRow = {
  topic: string
  content_relevance: number
  perspective_expansion: number
  linguistic_expression: number
  logical_structure: number
}

const activeTab = ref('record')
const summary = ref<Summary | null>(null)
const recommendations = ref<any[]>([])
const records = ref<any[]>([])
const matrix = ref<MatrixRow[]>([])
const breakdown = ref<any[]>([])
const languageProfile = ref<Record<string, number>>({})

const dimensions = [
  ['content_relevance', 'Content Relevance'],
  ['perspective_expansion', 'Perspective Expansion'],
  ['linguistic_expression', 'Linguistic Expression'],
  ['logical_structure', 'Logical Structure']
]

const scoreTrend = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { top: 48, right: 24, left: 40, bottom: 34 },
  legend: { right: 0, top: 0 },
  xAxis: { type: 'category', data: breakdown.value.map((_, index) => `#${index + 1}`) },
  yAxis: { type: 'value', min: 0, max: 5, interval: 1 },
  series: dimensions.map(([key, label], index) => ({
    name: label,
    type: 'line',
    data: breakdown.value.map((item) => item[key]),
    smooth: true,
    symbolSize: 7,
    lineStyle: { width: 2, color: ['#006d6f', '#5c8f43', '#c48b32', '#8a5a9c'][index] },
    itemStyle: { color: ['#006d6f', '#5c8f43', '#c48b32', '#8a5a9c'][index] }
  }))
}))

const radarOption = computed(() => ({
  radar: {
    indicator: Object.keys(languageProfile.value).map((key) => ({ name: key.replaceAll('_', ' '), max: 5 }))
  },
  series: [{ type: 'radar', data: [{ value: Object.values(languageProfile.value), name: 'Language Preference' }] }]
}))

const averageScore30 = computed(() => Math.round((summary.value?.average_score ?? 3.8) * 5 + 5))
const threeDayDelta = computed(() => {
  if (breakdown.value.length < 2) return 0.0
  const last = breakdown.value[breakdown.value.length - 1]
  const prev = breakdown.value[Math.max(0, breakdown.value.length - 4)] || breakdown.value[0]
  const avg = (item: any) => dimensions.reduce((sum, [key]) => sum + Number(item[key] || 0), 0) / dimensions.length
  return Number((avg(last) - avg(prev)).toFixed(1))
})

function heatColor(value: number) {
  if (value >= 4.2) return '#8bd4ae'
  if (value >= 3.8) return '#cfe8bf'
  if (value >= 3.4) return '#fff0b7'
  if (value >= 3.0) return '#ffd59f'
  return '#f19a9a'
}

function recordScore(row: any) {
  return Math.round(row.score * 5 + 5)
}

onMounted(async () => {
  summary.value = await apiGet('/dashboard/summary')
  recommendations.value = await apiGet('/dashboard/recommendations')
  records.value = await apiGet('/dashboard/records')
  matrix.value = await apiGet('/dashboard/topic-score-matrix')
  breakdown.value = await apiGet('/dashboard/score-breakdown')
  languageProfile.value = await apiGet('/dashboard/language-profile')
})
</script>

<template>
  <AppShell>
    <section class="dashboard-head panel panel-pad">
      <div>
        <p class="muted">Signed in as</p>
        <h1 class="simple-title">{{ summary?.alias || 'Writer' }}</h1>
        <p class="muted">User ID · {{ summary?.user_id || 'TAWEP-0000' }}</p>
      </div>
      <div class="dashboard-actions">
        <router-link class="btn ghost" to="/settings">Settings</router-link>
        <router-link class="btn ghost" to="/inbox">Inbox</router-link>
      </div>
    </section>

    <section class="dashboard-grid dashboard-recommendations">
      <div class="panel recommend-panel">
        <div>
          <h2 class="section-title">Recommended Academic Discussion Practice</h2>
          <p class="muted">Based on your topic score matrix, TAWEP prioritizes prompts that target weaker topics and scoring dimensions.</p>
        </div>
        <div class="rec-list">
          <router-link v-for="item in recommendations.slice(0, 2)" :key="item.question_no" class="rec-item" :to="`/${item.question_no}/prepare`">
            <span><strong>{{ item.question_no }}. {{ item.summary }}</strong><span>{{ item.topic }} · {{ item.reason }}</span></span>
            <strong>›</strong>
          </router-link>
          <router-link class="rec-item" to="/questionbank"><span><strong>Browse all Academic Discussion prompts</strong><span>Filter by difficulty, source, and topic</span></span><strong>›</strong></router-link>
        </div>
      </div>
      <aside class="panel avg-card">
        <p>Your Recent Average</p>
        <div class="avg-score">{{ averageScore30 }} <small>/30</small></div>
        <p>{{ summary?.practice_count || 0 }} total submissions</p>
        <p :class="threeDayDelta >= 0 ? 'change-up' : 'change-down'">{{ threeDayDelta >= 0 ? '↑' : '↓' }} {{ Math.abs(threeDayDelta).toFixed(1) }}</p>
        <p class="muted">recent 3-day dimension average</p>
      </aside>
    </section>

    <nav class="tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'record' }" @click="activeTab = 'record'">Record</button>
      <button class="tab-btn" :class="{ active: activeTab === 'language' }" @click="activeTab = 'language'">Language Preference</button>
      <button class="tab-btn" :class="{ active: activeTab === 'breakdown' }" @click="activeTab = 'breakdown'">Breakdown</button>
      <button class="tab-btn" :class="{ active: activeTab === 'matrix' }" @click="activeTab = 'matrix'">Matrix</button>
    </nav>

    <section v-if="activeTab === 'record'" class="panel">
      <div class="toolbar">
        <div class="control-row">
          <select class="select"><option>Academic Discussion</option></select>
          <select class="select"><option>All Scores</option><option>4.0+</option><option>Below 3.5</option></select>
        </div>
        <select class="select" style="max-width: 150px"><option>All Time</option><option>Last 30 Days</option></select>
      </div>
      <table class="data-table">
        <thead><tr><th>Date</th><th>Question</th><th>Topic</th><th class="center">Score<br />(/30)</th><th class="center">Change</th><th class="center">Report</th></tr></thead>
        <tbody>
          <tr v-for="(row, index) in records.slice(0, 8)" :key="row.session_id">
            <td>{{ new Date(row.submitted_at).toLocaleString() }}</td>
            <td>Academic Discussion #{{ row.question_no }}</td>
            <td>{{ row.topic }}</td>
            <td class="center">{{ recordScore(row) }}</td>
            <td class="center"><span :class="index === 3 ? 'change-down' : 'change-up'">{{ index === 3 ? '↓ 0.4' : index === 1 ? '-' : '↑ 0.3' }}</span></td>
            <td class="center"><router-link class="link-action" :to="`/${row.session_id}/report`">Open</router-link></td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-if="activeTab === 'language'" class="panel chart-box">
      <div class="chart-title"><h3>Language Preference</h3></div>
      <VChart style="height: 260px" :option="radarOption" autoresize />
    </section>

    <section v-if="activeTab === 'breakdown'" class="panel chart-box">
      <div class="chart-title"><h3>Recent 10 Evaluations</h3><strong :class="threeDayDelta >= 0 ? 'change-up' : 'change-down'">{{ threeDayDelta >= 0 ? '+' : '' }}{{ threeDayDelta.toFixed(1) }} last 3 days</strong></div>
      <VChart style="height: 260px" :option="scoreTrend" autoresize />
    </section>

    <section v-if="activeTab === 'matrix'" class="panel">
      <div class="panel-pad"><h3 style="margin: 0">Topic Score Matrix <span class="muted">(Average Score /5)</span></h3></div>
      <table class="data-table">
        <thead><tr><th>Topic</th><th v-for="[, label] in dimensions" :key="label" class="center">{{ label }}</th></tr></thead>
        <tbody>
          <tr v-for="row in matrix" :key="row.topic">
            <td>{{ row.topic }}</td>
            <td v-for="[key] in dimensions" :key="key" class="heat-cell" :style="{ background: heatColor(Number(row[key as keyof MatrixRow])) }">{{ row[key as keyof MatrixRow] }}</td>
          </tr>
        </tbody>
      </table>
      <div class="legend">
        <span class="legend-item"><i class="swatch" style="background:#8bd4ae"></i>4.2-5.0 Strong</span>
        <span class="legend-item"><i class="swatch" style="background:#cfe8bf"></i>3.8-4.1 Good</span>
        <span class="legend-item"><i class="swatch" style="background:#fff0b7"></i>3.4-3.7 Stable</span>
        <span class="legend-item"><i class="swatch" style="background:#ffd59f"></i>3.0-3.3 Weak</span>
        <span class="legend-item"><i class="swatch" style="background:#f19a9a"></i>Below 3.0 Needs Focus</span>
      </div>
    </section>
  </AppShell>
</template>
