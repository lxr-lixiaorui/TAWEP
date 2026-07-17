<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowRight, BookOpenText, Gift, HelpCircle, Search, Upload } from '@lucide/vue'
import AppShell from '../components/AppShell.vue'
import { apiGet } from '../api/client'

const { locale, t } = useI18n()
const filters = reactive({ difficulty: '', source: '', topic: '', exam_type: '' })
const questions = ref<any[]>([])
const topics = ref<string[]>([])
const loading = ref(true)
const loadError = ref(false)
const totalQuestions = ref<number | null>(null)
const recommendation = ref<any | null>(null)
let loadRequestId = 0

const examTypeOptions = computed(() => [
  {
    value: 'classic',
    label: t('bank.classic'),
    help: t('bank.classicHelp')
  },
  {
    value: 'reform_2026',
    label: t('bank.reform'),
    help: t('bank.reformHelp')
  }
])

const hasFilters = computed(() => Object.values(filters).some(Boolean))
const featuredQuestion = computed(() => {
  const recommended = recommendation.value
  if (!recommended) return null
  const question = questions.value.find((item) => item.question_no === recommended.question_no)
  return question ? { ...question, ...recommended } : null
})
const remainingQuestions = computed(() => questions.value)

async function loadQuestions() {
  const requestId = ++loadRequestId
  loading.value = true
  loadError.value = false
  recommendation.value = null
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  try {
    const recommendationParams = new URLSearchParams(params)
    recommendationParams.set('limit', '1')
    recommendationParams.set('locale', locale.value.startsWith('zh') ? 'zh' : 'en')
    const [loadedQuestions, recommendations] = await Promise.all([
      apiGet<any[]>(`/questions${params.toString() ? `?${params.toString()}` : ''}`),
      apiGet<any[]>(`/questions/recommendations?${recommendationParams.toString()}`).catch(() => [])
    ])
    if (requestId !== loadRequestId) return
    questions.value = loadedQuestions
    recommendation.value = recommendations[0] ?? null
    if (!hasFilters.value) totalQuestions.value = loadedQuestions.length
  } catch {
    if (requestId !== loadRequestId) return
    loadError.value = true
    questions.value = []
  } finally {
    if (requestId === loadRequestId) loading.value = false
  }
}

function selectExamType(value: string) {
  filters.exam_type = value
  loadQuestions()
}

function clearFilters() {
  filters.difficulty = ''
  filters.source = ''
  filters.topic = ''
  filters.exam_type = ''
  loadQuestions()
}

onMounted(async () => {
  try {
    topics.value = await apiGet('/questions/topics')
  } catch {
    topics.value = []
  }
  await loadQuestions()
})

watch(locale, () => {
  void loadQuestions()
})
</script>

<template>
  <AppShell>
    <header class="bank-heading">
      <div>
        <p class="eyebrow">{{ t('bank.overline', { count: totalQuestions ?? '—' }) }}</p>
        <h1>{{ t('bank.title') }}</h1>
        <p>{{ t('bank.subtitle') }}</p>
      </div>
      <div class="bank-contribute">
        <p class="bank-upload-reward"><Gift :size="16" /><span>{{ t('bank.uploadReward') }}</span></p>
        <router-link to="/createyourown" class="btn bank-upload"><Upload :size="17" />{{ t('bank.upload') }}</router-link>
      </div>
    </header>

    <section v-if="featuredQuestion && !loading" class="bank-featured">
      <div class="bank-featured-copy">
        <p><BookOpenText :size="16" />{{ t('bank.recommended') }}</p>
        <span>{{ featuredQuestion.topic }} · {{ featuredQuestion.exam_type === 'reform_2026' ? t('bank.reform') : t('bank.classic') }}</span>
        <h2>{{ featuredQuestion.summary }}</h2>
        <small>{{ featuredQuestion.reason || t('bank.recommendedReason') }}</small>
      </div>
      <div class="bank-featured-action">
        <span>{{ t('bank.minutes') }}</span>
        <router-link :to="`/${featuredQuestion.question_no}/prepare`" class="btn attention-cta">
          {{ t('bank.startNumber', { number: featuredQuestion.question_no }) }}<ArrowRight :size="17" />
        </router-link>
      </div>
    </section>

    <section class="bank-explorer">
      <div class="bank-filter-bar">
        <div class="bank-filter-title"><Search :size="18" /><strong>{{ t('bank.filterTitle') }}</strong></div>
        <div class="bank-filter-controls">
          <select v-model="filters.difficulty" class="select" :aria-label="t('bank.difficulty')" @change="loadQuestions">
            <option value="">{{ t('bank.allDifficulty') }}</option>
            <option value="easy">{{ t('bank.easy') }}</option>
            <option value="medium">{{ t('bank.medium') }}</option>
            <option value="hard">{{ t('bank.hard') }}</option>
          </select>
          <select v-model="filters.source" class="select" :aria-label="t('bank.source')" @change="loadQuestions">
            <option value="">{{ t('bank.allSources') }}</option>
            <option value="official">{{ t('bank.official') }}</option>
            <option value="user">{{ t('bank.userCreated') }}</option>
          </select>
          <select v-model="filters.topic" class="select" :aria-label="t('bank.topic')" @change="loadQuestions">
            <option value="">{{ t('bank.allTopics') }}</option>
            <option v-for="topic in topics" :key="topic" :value="topic">{{ topic }}</option>
          </select>
          <div class="bank-type-filter" :aria-label="t('bank.type')">
            <button type="button" :class="{ active: filters.exam_type === '' }" @click="selectExamType('')">{{ t('bank.allTypes') }}</button>
            <span v-for="option in examTypeOptions" :key="option.value">
              <button type="button" :class="{ active: filters.exam_type === option.value }" @click="selectExamType(option.value)">{{ option.label }}</button>
              <span class="help-tip" tabindex="0" :aria-label="option.help">
                <HelpCircle :size="15" />
                <span class="tooltip">{{ option.help }}</span>
              </span>
            </span>
          </div>
        </div>
      </div>

      <div v-if="loading" class="bank-loading" aria-live="polite">
        <span v-for="index in 5" :key="index"></span>
      </div>
      <div v-else-if="loadError" class="bank-empty" role="alert">
        <h2>{{ t('bank.loadFailed') }}</h2>
        <p>{{ t('bank.loadFailedBody') }}</p>
        <button class="btn" type="button" @click="loadQuestions">{{ t('bank.retry') }}</button>
      </div>
      <div v-else-if="!questions.length" class="bank-empty">
        <h2>{{ t('bank.noMatches') }}</h2>
        <p>{{ t('bank.noMatchesBody') }}</p>
        <button class="btn" type="button" @click="clearFilters">{{ t('bank.clear') }}</button>
      </div>
      <div v-else class="prompt-list">
        <router-link
          v-for="row in remainingQuestions"
          :key="row.question_no"
          :to="`/${row.question_no}/prepare`"
          class="prompt-row"
        >
          <span class="prompt-number">{{ String(row.question_no).padStart(2, '0') }}</span>
          <span class="prompt-main">
            <strong>{{ row.summary }}</strong>
            <small><i>{{ row.topic }}</i><i>{{ row.exam_type === 'reform_2026' ? t('bank.reform') : t('bank.classic') }}</i></small>
          </span>
          <span class="prompt-metric"><small>{{ t('bank.average') }}</small><strong>{{ row.avg_score || '--' }}</strong></span>
          <span class="prompt-metric"><small>{{ t('bank.words') }}</small><strong>{{ row.word_count || '--' }}</strong></span>
          <ArrowRight :size="18" />
        </router-link>
      </div>
    </section>
  </AppShell>
</template>
