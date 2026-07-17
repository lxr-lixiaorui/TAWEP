<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Award, CalendarDays, Send, TrendingUp } from '@lucide/vue'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPost } from '../api/client'
import { useAppStore } from '../stores/app'

type ExamResult = {
  id: string
  exam_date: string
  writing_score: number
  baseline_writing_score: number | null
  improvement: number | null
  created_at: string
  updated_at: string
}

type ExamOutcomeContext = {
  baseline_writing_score: number | null
  planned_exam_date: string | null
  latest_result: ExamResult | null
}

const app = useAppStore()
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const result = ref<ExamResult | null>(null)
const fixedBaseline = ref<number | null>(null)
const form = reactive({
  examDate: '',
  writingScore: '' as '' | number,
  baselineWritingScore: '' as '' | number
})

const today = new Date()
const maximumExamDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

const copy = computed(() => app.locale === 'zh' ? {
  overline: '真实成绩记录',
  title: '记录你的 TOEFL 写作成绩',
  lead: '成绩公布后，在这里登记正式写作分数。我们会根据你开始使用 TAWEP 时填写的基准分计算真实提分。',
  examDate: '考试日期',
  baseline: '使用 TAWEP 前的写作分数',
  baselineOptional: '基准写作分数（可选）',
  baselineHint: '如果注册时没有填写，可以在第一次登记成绩时补充。之后将作为固定基准。',
  official: '正式 TOEFL Writing 分数',
  scoreHint: '请输入 0–30 之间的整数。',
  disclosure: '成绩会先与账户关联保存。后续统计只会以汇总形式用于评估平均提分和改进服务。',
  submit: '保存成绩',
  saved: '成绩已保存',
  baselineCard: '起始分数',
  resultCard: '正式成绩',
  improvementCard: '真实提分',
  congratulations: (points: number) => `恭喜你提高了 ${points} 分`,
  stable: '这次成绩与起始分数相同，记录已保存。',
  recorded: '成绩已经记录，感谢你帮助我们改进 TAWEP。',
  ready: '填写正式成绩后即可计算提分。',
  noBaseline: '补充起始分数后即可计算提分。',
  loadError: '暂时无法读取成绩信息，请稍后重试。',
  saveError: '成绩保存失败，请检查填写内容后重试。'
} : {
  overline: 'Verified outcome',
  title: 'Report your TOEFL Writing score',
  lead: 'When your scores are released, record the official Writing result here. We calculate verified improvement from the baseline you provided when joining TAWEP.',
  examDate: 'Exam date',
  baseline: 'Writing score before TAWEP',
  baselineOptional: 'Baseline Writing score (optional)',
  baselineHint: 'If you skipped this during registration, add it with your first result. It then becomes your fixed baseline.',
  official: 'Official TOEFL Writing score',
  scoreHint: 'Enter a whole number from 0 to 30.',
  disclosure: 'The result is stored with your account. Future service metrics use aggregated outcomes to evaluate average improvement.',
  submit: 'Save result',
  saved: 'Result saved',
  baselineCard: 'Starting score',
  resultCard: 'Official score',
  improvementCard: 'Verified improvement',
  congratulations: (points: number) => `Congratulations, you improved by ${points} points`,
  stable: 'Your score matches the baseline. The result has been saved.',
  recorded: 'Your result is recorded. Thank you for helping us improve TAWEP.',
  ready: 'Enter your official score to calculate improvement.',
  noBaseline: 'Add a starting score to calculate improvement.',
  loadError: 'Your score information could not be loaded. Please try again later.',
  saveError: 'The result could not be saved. Check the values and try again.'
})

const outcomeMessage = computed(() => {
  if (!result.value) return ''
  if (result.value.improvement === null) return copy.value.noBaseline
  if (result.value.improvement > 0) return copy.value.congratulations(result.value.improvement)
  if (result.value.improvement === 0) return copy.value.stable
  return copy.value.recorded
})

onMounted(async () => {
  try {
    const context = await apiGet<ExamOutcomeContext>('/me/exam-outcome')
    fixedBaseline.value = context.baseline_writing_score
    result.value = context.latest_result
    form.examDate = context.planned_exam_date ?? context.latest_result?.exam_date ?? maximumExamDate
    form.writingScore = context.latest_result?.writing_score ?? ''
    form.baselineWritingScore = context.baseline_writing_score ?? context.latest_result?.baseline_writing_score ?? ''
  } catch {
    error.value = copy.value.loadError
  } finally {
    loading.value = false
  }
})

async function submitResult() {
  error.value = ''
  submitting.value = true
  try {
    result.value = await apiPost<ExamResult>('/me/exam-results', {
      exam_date: form.examDate,
      writing_score: Number(form.writingScore),
      baseline_writing_score: fixedBaseline.value ?? (form.baselineWritingScore === '' ? null : Number(form.baselineWritingScore))
    })
    if (fixedBaseline.value === null && result.value.baseline_writing_score !== null) {
      fixedBaseline.value = result.value.baseline_writing_score
    }
  } catch {
    error.value = copy.value.saveError
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppShell>
    <header class="score-report-heading">
      <p class="eyebrow">{{ copy.overline }}</p>
      <h1>{{ copy.title }}</h1>
      <p>{{ copy.lead }}</p>
    </header>

    <div class="score-report-layout">
      <form class="panel panel-pad score-report-form" @submit.prevent="submitResult">
        <label class="form-field">
          <span>{{ copy.examDate }}</span>
          <input v-model="form.examDate" class="input" type="date" :max="maximumExamDate" required />
        </label>
        <label class="form-field">
          <span>{{ fixedBaseline === null ? copy.baselineOptional : copy.baseline }}</span>
          <input
            v-model.number="form.baselineWritingScore"
            class="input"
            type="number"
            min="0"
            max="30"
            step="1"
            inputmode="numeric"
            :disabled="fixedBaseline !== null"
          />
          <small class="muted">{{ copy.baselineHint }}</small>
        </label>
        <label class="form-field">
          <span>{{ copy.official }}</span>
          <input v-model.number="form.writingScore" class="input score-input" type="number" min="0" max="30" step="1" inputmode="numeric" required />
          <small class="muted">{{ copy.scoreHint }}</small>
        </label>
        <p class="score-report-disclosure">{{ copy.disclosure }}</p>
        <p v-if="error" class="auth-message error" role="alert">{{ error }}</p>
        <button class="btn primary" type="submit" :disabled="loading || submitting || !form.examDate || form.writingScore === ''">
          <Send :size="17" />{{ copy.submit }}
        </button>
      </form>

      <section class="panel score-outcome" :class="{ positive: (result?.improvement ?? 0) > 0 }">
        <div class="score-outcome-icon" aria-hidden="true"><Award :size="30" /></div>
        <p class="eyebrow">{{ result ? copy.saved : copy.improvementCard }}</p>
        <h2>{{ outcomeMessage || (fixedBaseline !== null ? copy.ready : copy.noBaseline) }}</h2>
        <div class="score-comparison">
          <article><span>{{ copy.baselineCard }}</span><strong>{{ result?.baseline_writing_score ?? fixedBaseline ?? '—' }}</strong><small>/ 30</small></article>
          <TrendingUp :size="22" />
          <article><span>{{ copy.resultCard }}</span><strong>{{ result?.writing_score ?? '—' }}</strong><small>/ 30</small></article>
        </div>
        <div v-if="result?.improvement !== null && result?.improvement !== undefined" class="improvement-total">
          <span>{{ copy.improvementCard }}</span>
          <strong>{{ result.improvement > 0 ? '+' : '' }}{{ result.improvement }}</strong>
        </div>
        <div v-if="form.examDate" class="score-result-date"><CalendarDays :size="16" />{{ form.examDate }}</div>
      </section>
    </div>
  </AppShell>
</template>
