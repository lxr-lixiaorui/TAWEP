<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  Check,
  Circle,
  Clock3,
  Target,
  TrendingUp
} from '@lucide/vue'
import AppShell from '../components/AppShell.vue'
import { apiGet } from '../api/client'

type Summary = {
  alias: string
  user_id: string
  average_score: number
  practice_count: number
  weekly_practice_count: number
  credit: {
    balance: number
    total_planned_credit: number
  }
}

type MatrixRow = {
  topic: string
  content_relevance: number
  perspective_expansion: number
  linguistic_expression: number
  logical_structure: number
}

type DimensionKey = Exclude<keyof MatrixRow, 'topic'>

const { t } = useI18n()
const activeTab = ref('record')
const loading = ref(true)
const loadError = ref(false)
const summary = ref<Summary | null>(null)
const recommendations = ref<any[]>([])
const records = ref<any[]>([])
const matrix = ref<MatrixRow[]>([])
const breakdown = ref<any[]>([])
const languageProfile = ref<Record<string, number>>({})

const dimensionKeys: DimensionKey[] = [
  'content_relevance',
  'perspective_expansion',
  'linguistic_expression',
  'logical_structure'
]

const dimensions = computed(() =>
  dimensionKeys.map((key) => [key, t(`report.criteria.${key}`)] as const)
)

const primaryRecommendation = computed(() => recommendations.value[0] ?? {
  question_no: 1,
  summary: t('dashboard.fallbackPrompt'),
  topic: t('dashboard.generalTopic'),
  reason: t('dashboard.fallbackReason'),
  focus_dimension: 'logical_structure'
})

const latestBreakdown = computed(() => breakdown.value[breakdown.value.length - 1] ?? null)
const weakestDimension = computed<DimensionKey>(() => {
  const recommendedDimension = dimensionKeys.find((key) => key === primaryRecommendation.value.focus_dimension)
  if (recommendedDimension) return recommendedDimension
  const latest = latestBreakdown.value
  if (!latest) return 'logical_structure'
  return dimensionKeys.reduce((weakest, key) =>
    Number(latest[key] ?? 5) < Number(latest[weakest] ?? 5) ? key : weakest
  )
})
const weakestScore = computed(() => Number(latestBreakdown.value?.[weakestDimension.value] ?? 3.3))

const scoreTrend = computed(() => ({
  animation: false,
  tooltip: { trigger: 'axis' },
  grid: { top: 44, right: 18, left: 36, bottom: 28 },
  legend: { right: 0, top: 0, itemWidth: 14, itemHeight: 3 },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: breakdown.value.map((_, index) => `#${index + 1}`),
    axisLine: { lineStyle: { color: '#c9d5d7' } },
    axisTick: { show: false }
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 5,
    interval: 1,
    splitLine: { lineStyle: { color: '#e6ecec' } }
  },
  series: dimensions.value.map(([key, label], index) => ({
    name: label,
    type: 'line',
    data: breakdown.value.map((item) => item[key]),
    smooth: true,
    symbolSize: 6,
    lineStyle: { width: index === 3 ? 3 : 1.5, color: ['#0f766e', '#59874a', '#4078a8', '#d18a24'][index] },
    itemStyle: { color: ['#0f766e', '#59874a', '#4078a8', '#d18a24'][index] },
    emphasis: { focus: 'series' }
  }))
}))

const radarOption = computed(() => ({
  animation: false,
  radar: {
    indicator: Object.keys(languageProfile.value).map((key) => ({ name: key.replaceAll('_', ' '), max: 5 })),
    splitArea: { areaStyle: { color: ['#ffffff', '#f5f8f7'] } },
    axisName: { color: '#4f6264' }
  },
  series: [{
    type: 'radar',
    data: [{ value: Object.values(languageProfile.value), name: t('dashboard.languageProfile') }],
    areaStyle: { color: 'rgba(15, 118, 110, .16)' },
    lineStyle: { color: '#0f766e', width: 2 },
    itemStyle: { color: '#0f766e' }
  }]
}))

const averageScore30 = computed(() =>
  summary.value?.practice_count ? Math.round(summary.value.average_score * 5 + 5) : null
)
const weekPractices = computed(() => summary.value?.weekly_practice_count ?? 0)
const weeklyGoal = 10
const weeklyProgress = computed(() => Math.min(100, Math.round((weekPractices.value / weeklyGoal) * 100)))
const threeDayDelta = computed(() => {
  if (breakdown.value.length < 2) return 0
  const last = breakdown.value[breakdown.value.length - 1]
  const previous = breakdown.value[Math.max(0, breakdown.value.length - 4)] || breakdown.value[0]
  const average = (item: any) => dimensionKeys.reduce((sum, key) => sum + Number(item[key] || 0), 0) / dimensionKeys.length
  return Number((average(last) - average(previous)).toFixed(1))
})

function heatColor(value: number) {
  if (value >= 4.2) return '#a9dfc0'
  if (value >= 3.8) return '#d7edc8'
  if (value >= 3.4) return '#fff0b7'
  if (value >= 3.0) return '#ffd59f'
  return '#f2b1aa'
}

function recordScore(row: any) {
  return Math.round(row.score * 5 + 5)
}

onMounted(async () => {
  try {
    const [summaryResult, recommendationResult, recordResult, matrixResult, breakdownResult, profileResult] = await Promise.all([
      apiGet<Summary>('/dashboard/summary'),
      apiGet<any[]>('/dashboard/recommendations'),
      apiGet<any[]>('/dashboard/records'),
      apiGet<MatrixRow[]>('/dashboard/topic-score-matrix'),
      apiGet<any[]>('/dashboard/score-breakdown'),
      apiGet<Record<string, number>>('/dashboard/language-profile')
    ])
    summary.value = summaryResult
    recommendations.value = recommendationResult
    records.value = recordResult
    matrix.value = matrixResult
    breakdown.value = breakdownResult
    languageProfile.value = profileResult
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppShell>
    <header class="learning-welcome">
      <div>
        <p class="eyebrow">{{ t('dashboard.overline') }}</p>
        <h1>{{ t('dashboard.welcome', { name: summary?.alias || t('dashboard.writer') }) }}</h1>
        <p>{{ t('dashboard.welcomeBody') }}</p>
      </div>
      <div v-if="summary" class="credit-readout">
        <span>{{ t('dashboard.credits') }}</span>
        <strong>{{ summary.credit.balance }}</strong>
      </div>
    </header>

    <section v-if="loadError" class="dashboard-notice" role="alert">
      <strong>{{ t('dashboard.loadFailed') }}</strong>
      <span>{{ t('dashboard.loadFailedBody') }}</span>
    </section>

    <section class="next-practice" :class="{ loading }">
      <div class="practice-focus-copy">
        <div class="practice-meta">
          <span><Target :size="16" />{{ t('dashboard.recommendedNext') }}</span>
          <span><Clock3 :size="16" />{{ t('dashboard.minutes', { count: 12 }) }}</span>
        </div>
        <p class="practice-kicker">{{ primaryRecommendation.topic }} · {{ t('dashboard.academicDiscussion') }}</p>
        <h2>{{ primaryRecommendation.summary }}</h2>
        <p class="practice-reason">{{ primaryRecommendation.reason }}</p>
        <div class="practice-actions">
          <router-link class="btn primary attention-cta" :to="`/${primaryRecommendation.question_no}/prepare`">
            {{ t('dashboard.startQuestion', { number: primaryRecommendation.question_no }) }}
            <ArrowRight :size="17" />
          </router-link>
          <router-link class="btn quiet" to="/questionbank">{{ t('dashboard.chooseAnother') }}</router-link>
        </div>
      </div>

      <aside class="practice-focus-meter">
        <p>{{ t('dashboard.currentFocus') }}</p>
        <div class="focus-dimension">
          <span>{{ t(`report.criteria.${weakestDimension}`) }}</span>
          <strong>{{ weakestScore.toFixed(1) }}<small>/5</small></strong>
        </div>
        <div class="focus-track"><i :style="{ width: `${(weakestScore / 5) * 100}%` }"></i></div>
        <p class="focus-goal">{{ t('dashboard.focusGoal') }}</p>
      </aside>
    </section>

    <section class="momentum-strip" aria-label="Practice momentum">
      <article>
        <TrendingUp :size="20" />
        <span>{{ t('dashboard.currentAverage') }}</span>
        <strong v-if="averageScore30 !== null">{{ averageScore30 }}<small>/30</small></strong>
        <strong v-else>--<small>/30</small></strong>
        <em v-if="averageScore30 === null">{{ t('dashboard.firstScore') }}</em>
        <em v-else :class="threeDayDelta >= 0 ? 'positive' : 'negative'">
          {{ threeDayDelta >= 0 ? '+' : '' }}{{ threeDayDelta.toFixed(1) }} {{ t('dashboard.recent') }}
        </em>
      </article>
      <article>
        <BookOpen :size="20" />
        <span>{{ t('dashboard.completedResponses') }}</span>
        <strong>{{ summary?.practice_count ?? '--' }}</strong>
        <em>{{ t('dashboard.savedReports') }}</em>
      </article>
      <article class="weekly-momentum">
        <BarChart3 :size="20" />
        <span>{{ t('dashboard.weeklyRhythm') }}</span>
        <strong>{{ weekPractices }}<small>/{{ weeklyGoal }}</small></strong>
        <div class="weekly-track"><i :style="{ width: `${weeklyProgress}%` }"></i></div>
      </article>
    </section>

    <section class="dashboard-learning-grid">
      <div class="learning-insight">
        <div class="learning-section-head">
          <div>
            <p class="eyebrow">{{ t('dashboard.progress') }}</p>
            <h2>{{ t('dashboard.lastTen') }}</h2>
          </div>
          <span :class="threeDayDelta >= 0 ? 'positive' : 'negative'">
            {{ threeDayDelta >= 0 ? '+' : '' }}{{ threeDayDelta.toFixed(1) }}
          </span>
        </div>
        <VChart v-if="breakdown.length" class="dashboard-trend-chart" :option="scoreTrend" autoresize />
        <div v-else class="dashboard-empty compact">
          <TrendingUp :size="24" />
          <p>{{ t('dashboard.trendEmpty') }}</p>
        </div>
      </div>

      <aside class="weekly-plan">
        <p class="eyebrow">{{ t('dashboard.thisWeek') }}</p>
        <h2>{{ t('dashboard.smallPlan') }}</h2>
        <div class="plan-progress"><i :style="{ width: `${weeklyProgress}%` }"></i></div>
        <ol>
          <li :class="{ complete: weekPractices >= 1 }">
            <Check v-if="weekPractices >= 1" :size="16" />
            <Circle v-else :size="16" />
            <span>{{ t('dashboard.planPractice') }}</span>
          </li>
          <li :class="{ complete: weekPractices >= 2 }">
            <Check v-if="weekPractices >= 2" :size="16" />
            <Circle v-else :size="16" />
            <span>{{ t('dashboard.planGrammar') }}</span>
          </li>
          <li :class="{ complete: weekPractices >= 3 }">
            <Check v-if="weekPractices >= 3" :size="16" />
            <Circle v-else :size="16" />
            <span>{{ t('dashboard.planRetry') }}</span>
          </li>
        </ol>
      </aside>
    </section>

    <nav class="dashboard-secondary-tabs" aria-label="Dashboard views">
      <button :class="{ active: activeTab === 'record' }" @click="activeTab = 'record'">{{ t('dashboard.recentWork') }}</button>
      <button :class="{ active: activeTab === 'matrix' }" @click="activeTab = 'matrix'">{{ t('dashboard.topicFocus') }}</button>
      <button :class="{ active: activeTab === 'language' }" @click="activeTab = 'language'">{{ t('dashboard.languageProfile') }}</button>
    </nav>

    <section v-if="activeTab === 'record'" class="dashboard-detail">
      <div class="detail-heading">
        <div><p class="eyebrow">{{ t('dashboard.history') }}</p><h2>{{ t('dashboard.recentSubmissions') }}</h2></div>
        <router-link class="text-link" to="/questionbank">{{ t('dashboard.startNew') }}<ArrowRight :size="16" /></router-link>
      </div>
      <div v-if="records.length" class="recent-work-list">
        <router-link v-for="row in records.slice(0, 6)" :key="row.session_id" :to="`/${row.session_id}/report`" class="recent-work-row">
          <span class="recent-work-date">{{ new Date(row.submitted_at).toLocaleDateString() }}</span>
          <span><strong>{{ t('dashboard.questionNumber', { number: row.question_no }) }}</strong><small>{{ row.topic }}</small></span>
          <strong class="recent-work-score">{{ recordScore(row) }}<small>/30</small></strong>
          <ArrowRight :size="17" />
        </router-link>
      </div>
      <div v-else class="dashboard-empty">
        <BookOpen :size="28" />
        <h3>{{ t('dashboard.noSubmissions') }}</h3>
        <p>{{ t('dashboard.noSubmissionsBody') }}</p>
        <router-link class="btn primary" to="/questionbank">{{ t('dashboard.findPrompt') }}</router-link>
      </div>
    </section>

    <section v-if="activeTab === 'language'" class="dashboard-detail chart-detail">
      <div class="detail-heading"><div><p class="eyebrow">{{ t('dashboard.profile') }}</p><h2>{{ t('dashboard.languageProfile') }}</h2></div></div>
      <VChart class="dashboard-radar-chart" :option="radarOption" autoresize />
    </section>

    <section v-if="activeTab === 'matrix'" class="dashboard-detail">
      <div class="detail-heading"><div><p class="eyebrow">{{ t('dashboard.byTopic') }}</p><h2>{{ t('dashboard.topicFocus') }}</h2></div></div>
      <div class="matrix-scroll">
        <table class="data-table focus-matrix">
          <thead><tr><th>{{ t('dashboard.topic') }}</th><th v-for="[, label] in dimensions" :key="label" class="center">{{ label }}</th></tr></thead>
          <tbody>
            <tr v-for="row in matrix" :key="row.topic">
              <td>{{ row.topic }}</td>
              <td v-for="[key] in dimensions" :key="key" class="heat-cell" :style="{ background: heatColor(Number(row[key])) }">{{ row[key] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </AppShell>
</template>
