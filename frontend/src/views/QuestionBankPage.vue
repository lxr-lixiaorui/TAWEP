<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowRight, BookOpenText, HelpCircle, Search, Upload } from '@lucide/vue'
import AppShell from '../components/AppShell.vue'
import { apiGet } from '../api/client'

const { t } = useI18n()
const filters = reactive({ difficulty: '', source: '', topic: '', exam_type: '' })
const questions = ref<any[]>([])
const topics = ref<string[]>([])
const loading = ref(true)
const loadError = ref(false)
const totalQuestions = ref(96)

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
const featuredQuestion = computed(() => hasFilters.value ? null : (questions.value[0] ?? null))
const remainingQuestions = computed(() => featuredQuestion.value ? questions.value.slice(1) : questions.value)

async function loadQuestions() {
  loading.value = true
  loadError.value = false
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  try {
    questions.value = await apiGet(`/questions${params.toString() ? `?${params.toString()}` : ''}`)
    if (!hasFilters.value) totalQuestions.value = questions.value.length || totalQuestions.value
  } catch {
    loadError.value = true
    questions.value = []
  } finally {
    loading.value = false
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
</script>

<template>
  <AppShell>
    <header class="bank-heading">
      <div>
        <p class="eyebrow">{{ t('bank.overline', { count: totalQuestions }) }}</p>
        <h1>{{ t('bank.title') }}</h1>
        <p>{{ t('bank.subtitle') }}</p>
      </div>
      <router-link to="/createyourown" class="btn bank-upload"><Upload :size="17" />{{ t('bank.upload') }}</router-link>
    </header>

    <section v-if="featuredQuestion && !loading" class="bank-featured">
      <div class="bank-featured-copy">
        <p><BookOpenText :size="16" />{{ t('bank.recommended') }}</p>
        <span>{{ featuredQuestion.topic }} · {{ featuredQuestion.exam_type === 'reform_2026' ? t('bank.reform') : t('bank.classic') }}</span>
        <h2>{{ featuredQuestion.summary }}</h2>
        <small>{{ t('bank.recommendedReason') }}</small>
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
