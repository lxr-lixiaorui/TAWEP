<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { CircleHelp, MessageSquare, TrendingDown, TrendingUp, X } from '@lucide/vue'
import { useMessage, useNotification } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import { apiDownload, apiGet, apiPost } from '../api/client'
import { useAppStore } from '../stores/app'

const props = defineProps<{ activeTab?: string }>()
const route = useRoute()
const router = useRouter()
const message = useMessage()
const notification = useNotification()
const appStore = useAppStore()
const { t } = useI18n()
const sessionId = String(route.params.sessionId)
const isExampleSession = sessionId === '00000000-0000-4000-8000-000000000008'
const active = ref(props.activeTab || 'answer')
const session = ref<any | null>(null)
const question = ref<any | null>(null)
const report = ref<any | null>(null)
const evaluation = ref<any | null>(null)
const grammar = ref<any[]>([])
const answer = ref('')
const submittedAnswer = ref('')
const submitting = ref(false)
const feedbackOpen = ref(false)
const feedbackSubmitting = ref(false)
const feedbackType = ref<'too_high' | 'too_low' | 'other' | ''>('')
const feedbackComment = ref('')
const feedbackConsent = ref(false)
const feedbackStatus = ref<{ submitted: boolean; feedback_type?: string; created_at?: string }>({ submitted: false })
const feedbackStatusLoaded = ref(false)
const timeLeft = ref<number | null>(null)
const hideTimer = ref(false)
const hideWordCount = ref(false)
const answerInput = ref<HTMLTextAreaElement | null>(null)
let timerId: number | undefined
let evaluationPollId: number | undefined
let evaluationRequestActive = false
let completionNotified = false

async function downloadReport() {
  try {
    await apiDownload(`/sessions/${sessionId}/download`, `tawep-report-${sessionId}.html`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Download failed')
  }
}

const wordCount = computed(() => answer.value.trim().split(/\s+/).filter(Boolean).length)
const timerLabel = computed(() => {
  if (timeLeft.value === null) return 'Unlimited'
  const minutes = Math.floor(timeLeft.value / 60)
  const seconds = timeLeft.value % 60
  return `00:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})
const timerUrgent = computed(() => timeLeft.value !== null && timeLeft.value <= 300)
const evaluationActive = computed(() => ['queued', 'evaluating', 'retrying'].includes(evaluation.value?.status))
const evaluationFailed = computed(() => evaluation.value?.status === 'failed')
const partialReport = computed(() => evaluation.value?.partial_report ?? {})
const availableSections = computed(() => new Set<string>(evaluation.value?.available_sections ?? []))
const displayGrammar = computed(() => grammar.value.length ? grammar.value : (partialReport.value.grammar_analysis ?? []))
const stageLabel = computed(() => evaluation.value?.stage === 'rewrite_comparison'
  ? t('rewrite.stage')
  : t(`report.stages.${evaluation.value?.stage || 'queued'}`))
const elapsedLabel = computed(() => {
  const seconds = Number(evaluation.value?.elapsed_seconds ?? 0)
  const minutes = Math.floor(seconds / 60)
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
})
const topActionLabel = computed(() => {
  if (submitting.value) return 'Evaluating...'
  return report.value || evaluation.value ? 'Report' : 'Submit'
})
const orderedMessages = computed(() => [...(question.value?.messages ?? [])].sort((a, b) => a.sort_order - b.sort_order))
const professorMessage = computed(() => orderedMessages.value.find(item => item.speaker_role === 'professor') ?? orderedMessages.value[0])
const studentMessages = computed(() => orderedMessages.value.filter(item => item.speaker_role !== 'professor'))
const displayReport = computed(() => report.value ?? partialReport.value)
const reportRows = computed(() => [
  [t('report.criteria.content_relevance'), displayReport.value?.components?.content_relevance ?? null, 'content_relevance'],
  [t('report.criteria.perspective_expansion'), displayReport.value?.components?.perspective_expansion ?? null, 'perspective_expansion'],
  [t('report.criteria.linguistic_expression'), displayReport.value?.components?.linguistic_expression ?? null, 'linguistic_expression'],
  [t('report.criteria.logical_structure'), displayReport.value?.components?.logical_structure ?? null, 'logical_structure']
])
const reportCards = computed(() => reportRows.value.map((row) => {
  const key = String(row[2])
  const score = row[1] === null ? null : Number(row[1])
  return {
    label: String(row[0]),
    key,
    score,
    percent: score === null ? 0 : Math.max(0, Math.min(100, (score / 5) * 100)),
    problem: displayReport.value?.problems?.[key] || '',
    improvement: displayReport.value?.improvements?.[key] || ''
  }
}))
const scoredReportCards = computed(() => reportCards.value.filter(card => card.score !== null))
const strongestReportCard = computed(() => [...scoredReportCards.value].sort((a, b) => Number(b.score) - Number(a.score))[0])
const sortedFocusCards = computed(() => [...scoredReportCards.value].sort((a, b) => Number(a.score) - Number(b.score)))
const focusReportCard = computed(() => sortedFocusCards.value[0])
const priorityActionCards = computed(() => [...reportCards.value].sort((a, b) => {
  if (a.score === null && b.score === null) return 0
  if (a.score === null) return 1
  if (b.score === null) return -1
  return a.score - b.score
}))
const grammarIssueCount = computed(() => displayGrammar.value.filter((item: any) => item.issue_type === 'grammar').length)
const answerForAnalysis = computed(() => submittedAnswer.value || answer.value || session.value?.answer_text || displayGrammar.value.map((item: any) => item.original_text).filter(Boolean).join(' '))
const spellingIssueCount = computed(() => displayGrammar.value.filter((item: any) => item.issue_type === 'spelling').length)
const annotatedAnswer = computed(() => buildAnnotatedAnswer(answerForAnalysis.value, displayGrammar.value))
const grammarAnalysisPath = computed(() => '/' + sessionId + '/grammaranalysis')
const rewritePath = computed(() => '/' + sessionId + '/rewrite')
const rewriteSections = computed(() => {
  const sections = displayReport.value?.rewrite_comparison?.sections
  if (Array.isArray(sections) && sections.length) return sections
  if (displayReport.value?.ai_rewrite && answerForAnalysis.value) {
    return [{
      role: 'position',
      original_text: answerForAnalysis.value,
      rewritten_text: displayReport.value.ai_rewrite,
      highlights: []
    }]
  }
  return []
})
const canSubmitFeedback = computed(() => Boolean(
  feedbackType.value
  && feedbackConsent.value
  && (feedbackType.value !== 'other' || feedbackComment.value.trim())
))

async function loadFeedbackStatus() {
  if (isExampleSession || !report.value) return
  try {
    feedbackStatus.value = await apiGet(`/sessions/${sessionId}/feedback`)
  } catch {
    feedbackStatus.value = { submitted: false }
  } finally {
    feedbackStatusLoaded.value = true
  }
}

function openFeedback() {
  feedbackType.value = ''
  feedbackComment.value = ''
  feedbackConsent.value = false
  feedbackOpen.value = true
}

async function submitFeedback() {
  if (!canSubmitFeedback.value || feedbackSubmitting.value) return
  if (feedbackType.value === 'other' && !feedbackComment.value.trim()) {
    message.warning(t('report.feedback.otherRequired'))
    return
  }
  feedbackSubmitting.value = true
  try {
    feedbackStatus.value = await apiPost(`/sessions/${sessionId}/feedback`, {
      feedback_type: feedbackType.value,
      comment: feedbackComment.value.trim() || null,
      consent_to_share: true
    })
    feedbackStatusLoaded.value = true
    feedbackOpen.value = false
    message.success(t('report.feedback.success'))
  } catch (error) {
    message.error(error instanceof Error ? error.message : t('report.feedback.otherRequired'))
  } finally {
    feedbackSubmitting.value = false
  }
}

function sectionReady(name: string) {
  return Boolean(report.value) || availableSections.value.has(name)
}

function avatarFor(role: string, index = 0) {
  if (role === 'professor') return '/static/images/img_teacher_diaz.png'
  return index === 0 ? '/static/images/img_student_paul.png' : '/static/images/img_student_kelly.png'
}

function stopTimer() {
  if (timerId) {
    window.clearInterval(timerId)
    timerId = undefined
  }
  timeLeft.value = null
  hideTimer.value = true
}

function startTimer() {
  if (!session.value?.time_limit_seconds || timerId || report.value) return
  timeLeft.value = session.value.time_limit_seconds
  timerId = window.setInterval(() => {
    if (timeLeft.value === null) return
    timeLeft.value = Math.max(0, timeLeft.value - 1)
    if (timeLeft.value === 0) {
      stopTimer()
      if (!answer.value.includes('AllowOvertime:True')) {
        void submit()
      }
    }
  }, 1000)
}

async function submit() {
  if (submitting.value || report.value || evaluationActive.value) return
  submittedAnswer.value = answer.value
  submitting.value = true
  try {
    evaluation.value = await apiPost(`/sessions/${sessionId}/submit`, {
      answer_text: answer.value,
      report_locale: appStore.locale
    })
    stopTimer()
    active.value = 'report'
    await router.replace(`/${sessionId}/report`)
    startEvaluationPolling()
  } catch (error) {
    notification.error({ title: 'Unable to start evaluation', content: String(error).includes('INSUFFICIENT_CREDIT') ? 'Each evaluation costs 3 credits.' : 'Please try again.' })
  } finally {
    submitting.value = false
  }
}

async function handleTopAction() {
  if (report.value || evaluation.value) {
    active.value = 'report'
    await router.replace(`/${sessionId}/report`)
    return
  }
  await submit()
}

async function goToTab(tab: string) {
  const suffix = {
    answer: 'answerpage',
    report: 'report',
    rewrite: 'rewrite',
    grammar: 'grammaranalysis',
    download: 'download'
  }[tab]
  if (!suffix) return
  active.value = tab
  await router.push(`/${sessionId}/${suffix}`)
}

function stopEvaluationPolling() {
  if (evaluationPollId) {
    window.clearInterval(evaluationPollId)
    evaluationPollId = undefined
  }
}

async function refreshEvaluation() {
  if (!evaluation.value?.id || evaluationRequestActive) return
  evaluationRequestActive = true
  try {
    evaluation.value = await apiGet(`/evaluations/${evaluation.value.id}`)
    if (evaluation.value.status === 'completed') {
      report.value = await apiGet(`/sessions/${sessionId}/report`)
      grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
      stopEvaluationPolling()
      if (!completionNotified) {
        completionNotified = true
        message.success(t('report.ready'))
      }
    } else if (evaluation.value.status === 'failed') {
      stopEvaluationPolling()
    }
  } finally {
    evaluationRequestActive = false
  }
}

function startEvaluationPolling() {
  stopEvaluationPolling()
  void refreshEvaluation()
  if (evaluationActive.value) {
    evaluationPollId = window.setInterval(() => void refreshEvaluation(), 2000)
  }
}

async function loadEvaluationForSession() {
  try {
    evaluation.value = await apiGet(`/evaluations/by-session/${sessionId}`)
    if (evaluation.value.status === 'completed') {
      report.value = await apiGet(`/sessions/${sessionId}/report`)
      grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
    } else if (evaluationActive.value) {
      startEvaluationPolling()
    }
  } catch {
    try {
      report.value = await apiGet(`/sessions/${sessionId}/report`)
      grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
    } catch {
      report.value = null
    }
  }
}

async function discardAndQuit() {
  await router.push(question.value?.question_no ? `/${question.value.question_no}/prepare` : '/questionbank')
}

async function focusEditor() {
  await nextTick()
  answerInput.value?.focus()
}

function runEditorCommand(command: 'cut' | 'undo' | 'redo') {
  void focusEditor()
  document.execCommand(command)
}

async function pasteFromClipboard() {
  await focusEditor()
  try {
    const text = await navigator.clipboard.readText()
    const input = answerInput.value
    if (!input) return
    const start = input.selectionStart
    const end = input.selectionEnd
    answer.value = `${answer.value.slice(0, start)}${text}${answer.value.slice(end)}`
    await nextTick()
    input.setSelectionRange(start + text.length, start + text.length)
  } catch {
    message.warning('Browser blocked clipboard paste. Use Ctrl+V instead.')
  }
}

function issueLabel(type: string) {
  return {
    grammar: appStore.locale === 'zh' ? '语法问题' : 'Grammar issue',
    spelling: appStore.locale === 'zh' ? '拼写问题' : 'Spelling issue',
    wording: appStore.locale === 'zh' ? '措辞问题' : 'Wording issue'
  }[type] || (appStore.locale === 'zh' ? '语言问题' : 'Language issue')
}

function issueClass(type: string) {
  return ['grammar', 'spelling', 'wording'].includes(type) ? type : 'wording'
}

function buildAnnotatedAnswer(text: string, issues: any[]) {
  if (!text) return []
  const ranges: any[] = []
  const sentences = Array.from(text.matchAll(/[^.!?]+(?:[.!?]+["']*|$)/gm)).map((match) => {
    const raw = match[0]
    const leading = raw.length - raw.trimStart().length
    return { start: (match.index || 0) + leading, text: raw.trim() }
  })
  issues.forEach((issue) => {
    const rawNeedle = String(issue.original_text || '').trim()
    if (!rawNeedle) return
    let start = Number.isInteger(issue.start_offset) ? Number(issue.start_offset) : -1
    let end = Number.isInteger(issue.end_offset) ? Number(issue.end_offset) : -1
    if (start < 0 || end <= start || text.slice(start, end).toLocaleLowerCase() !== rawNeedle.toLocaleLowerCase()) {
      start = -1
      const sentence = sentences[Number(issue.sentence_index || 1) - 1]
      if (sentence) {
        const matches = Array.from(sentence.text.matchAll(new RegExp(rawNeedle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')))
        const occurrence = Math.max(1, Number(issue.occurrence_index || 1))
        const match = matches[occurrence - 1]
        if (match?.index !== undefined) start = sentence.start + match.index
      }
      end = start + rawNeedle.length
    }
    if (start === -1) return
    ranges.push({ start, end, issues: [issue] })
  })
  ranges.sort((a, b) => a.start - b.start)
  const merged: any[] = []
  for (const range of ranges) {
    const previous = merged[merged.length - 1]
    if (previous && range.start < previous.end) {
      previous.end = Math.max(previous.end, range.end)
      previous.issues.push(...range.issues)
    } else {
      merged.push(range)
    }
  }
  const parts: any[] = []
  let position = 0
  merged.forEach((range) => {
    if (range.start > position) parts.push({ text: text.slice(position, range.start) })
    parts.push({
      text: text.slice(range.start, range.end),
      issues: range.issues,
      types: [...new Set(range.issues.map((issue: any) => issueClass(issue.issue_type)))]
    })
    position = range.end
  })
  if (position < text.length) parts.push({ text: text.slice(position) })
  return parts
}

function buildRewriteParts(text: string, highlights: any[], side: 'original' | 'rewritten') {
  if (!text) return []
  const key = side === 'original' ? 'original_text' : 'rewritten_text'
  const ranges: any[] = []
  let cursor = 0
  for (const highlight of highlights || []) {
    const needle = String(highlight?.[key] || '').trim()
    if (!needle) continue
    let start = text.indexOf(needle, cursor)
    if (start === -1) start = text.indexOf(needle)
    if (start === -1) continue
    const end = start + needle.length
    if (!ranges.some(range => start < range.end && end > range.start)) {
      ranges.push({ start, end, type: highlight.highlight_type })
      cursor = end
    }
  }
  ranges.sort((a, b) => a.start - b.start)
  const parts: any[] = []
  let position = 0
  for (const range of ranges) {
    if (range.start > position) parts.push({ text: text.slice(position, range.start) })
    parts.push({ text: text.slice(range.start, range.end), type: range.type })
    position = range.end
  }
  if (position < text.length) parts.push({ text: text.slice(position) })
  return parts
}

onMounted(async () => {
  session.value = await apiGet(`/sessions/${sessionId}`)
  question.value = await apiGet(`/questions/${session.value.question_no}`)
  answer.value = session.value.answer_text || ''
  submittedAnswer.value = answer.value
  if (active.value !== 'answer') {
    stopTimer()
    await loadEvaluationForSession()
  } else {
    if (['submitted', 'evaluated', 'failed'].includes(session.value?.status)) {
      await loadEvaluationForSession()
    }
    if (['created', 'in_progress'].includes(session.value?.status)) startTimer()
  }
})

onUnmounted(() => {
  if (timerId) window.clearInterval(timerId)
  stopEvaluationPolling()
})

watch(() => props.activeTab, (next) => {
  if (next && next !== active.value) {
    active.value = next
  }
})

watch(active, async (next) => {
  if (next !== 'answer') stopTimer()
  if (next === 'report' && !report.value && !evaluation.value) {
    await loadEvaluationForSession()
  }
  if (next === 'grammar' && grammar.value.length === 0 && evaluation.value?.status === 'completed') {
    grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
  }
})

watch(report, (next) => {
  if (next) void loadFeedbackStatus()
})
</script>

<template>
  <section v-if="active === 'answer'" class="toefl-exam-page">
    <div class="toefl-shell">
      <header class="toefl-topbar">
        <div class="toefl-logo">TAWEP</div>
        <button class="toefl-next" :disabled="submitting" @click="handleTopAction">{{ topActionLabel }}</button>
      </header>

      <div class="toefl-sectionbar">
        <span>Section 1 of 1</span>
        <div v-if="!report" class="toefl-section-actions">
          <span v-if="!hideTimer" class="toefl-time" :class="{ urgent: timerUrgent }">{{ timerLabel }}</span>
          <button class="toefl-link" @click="hideTimer = !hideTimer">{{ hideTimer ? 'Show Timer' : 'Hide Timer' }}</button>
        </div>
        <span v-else class="toefl-ready">Report is ready</span>
      </div>

      <div class="toefl-board">
        <aside class="toefl-left-pane">
          <div class="toefl-instructions">
            <p>Your professor is teaching a class on {{ question?.topic?.toLowerCase() || 'an academic topic' }}.</p>
            <p>Write a post responding to the professor's question.</p>
            <p>In your response, you should do the following.</p>
            <ul>
              <li>Express and support your opinion.</li>
              <li>Make a contribution to the discussion in your own words.</li>
            </ul>
            <p>An effective response will contain at least 100 words.</p>
          </div>

          <div v-if="professorMessage" class="toefl-professor">
            <img :src="avatarFor('professor')" :alt="professorMessage.speaker_name" class="toefl-avatar large" />
            <strong>{{ professorMessage.speaker_name }}</strong>
          </div>

          <p class="toefl-professor-text">{{ professorMessage?.content }}</p>
        </aside>

        <main class="toefl-right-pane">
          <div class="toefl-students">
            <article v-for="(msg, index) in studentMessages" :key="msg.sort_order" class="toefl-student-row">
              <div class="toefl-person">
                <img :src="avatarFor(msg.speaker_role, index)" :alt="msg.speaker_name" class="toefl-avatar" />
                <span>{{ msg.speaker_name }}</span>
              </div>
              <p>{{ msg.content }}</p>
            </article>
          </div>

          <div class="toefl-editor-shell">
            <div class="toefl-editor-toolbar">
              <div class="toefl-edit-buttons">
                <button class="toefl-tool active" @click="runEditorCommand('cut')">Cut</button>
                <button class="toefl-tool" @click="pasteFromClipboard">Paste</button>
                <button class="toefl-tool" @click="runEditorCommand('undo')">Undo</button>
                <button class="toefl-tool" @click="runEditorCommand('redo')">Redo</button>
              </div>
              <div class="toefl-word-tools">
                <button class="toefl-link" @click="hideWordCount = !hideWordCount">{{ hideWordCount ? 'Show Word Count' : 'Hide Word Count' }}</button>
                <span v-if="!hideWordCount">{{ wordCount }}</span>
              </div>
            </div>
            <textarea
              ref="answerInput"
              v-model="answer"
              class="toefl-textarea"
              placeholder="Type your response here."
            ></textarea>
            <div class="toefl-editor-footer">
              <button class="btn ghost small" @click="discardAndQuit">Discard and Quit</button>
            </div>
          </div>
        </main>
      </div>
    </div>
  </section>

  <AppShell v-else>
    <nav class="tabs">
      <button class="tab-btn" :class="{ active: active === 'answer' }" @click="goToTab('answer')">{{ t('report.tabs.answer') }}</button>
      <button class="tab-btn" :class="{ active: active === 'report' }" @click="goToTab('report')">{{ t('report.tabs.report') }}</button>
      <button class="tab-btn" :class="{ active: active === 'rewrite' }" @click="goToTab('rewrite')">{{ t('rewrite.tab') }}</button>
      <button class="tab-btn" :class="{ active: active === 'grammar' }" @click="goToTab('grammar')">{{ t('report.tabs.grammar') }}</button>
      <button class="tab-btn" :class="{ active: active === 'download' }" @click="goToTab('download')">{{ t('report.tabs.download') }}</button>
    </nav>

    <article v-if="active === 'report'" class="report-modern">
      <section
        v-if="evaluationActive || evaluationFailed"
        class="evaluation-status panel"
        :class="{ failed: evaluationFailed }"
        aria-live="polite"
      >
        <div v-if="evaluationActive" class="evaluation-spinner" aria-hidden="true"><span></span></div>
        <div class="evaluation-status-copy">
          <strong>{{ evaluationFailed ? t('report.failed') : t('report.evaluating') }}</strong>
          <span>{{ evaluationFailed ? t('report.refunded') : stageLabel }}</span>
        </div>
        <div v-if="evaluationActive" class="evaluation-time">
          <strong>{{ t('report.typical') }}</strong>
          <span>{{ t('report.elapsed') }} {{ elapsedLabel }}</span>
        </div>
        <div v-if="evaluationActive" class="evaluation-steps" aria-label="Evaluation progress">
          <span :class="{ ready: sectionReady('problems'), current: evaluation?.stage === 'problems' }">1</span>
          <i></i>
          <span :class="{ ready: sectionReady('scores'), current: evaluation?.stage === 'scores' }">2</span>
          <i></i>
          <span :class="{ ready: sectionReady('improvements'), current: evaluation?.stage === 'improvements' }">3</span>
          <i></i>
          <span :class="{ ready: sectionReady('rewrite_comparison'), current: ['ai_rewrite', 'rewrite_comparison'].includes(evaluation?.stage) }">4</span>
          <i></i>
          <span :class="{ ready: sectionReady('grammar_analysis'), current: evaluation?.stage === 'grammar_analysis' }">5</span>
        </div>
      </section>

      <header class="report-hero focused">
        <div class="report-hero-copy">
          <p class="eyebrow">{{ t('report.evaluationReport') }}</p>
          <h1 v-if="focusReportCard" class="section-reveal">{{ t('report.focusOn', { criterion: focusReportCard.label }) }}</h1>
          <h1 v-else>{{ t('report.evaluating') }}</h1>
          <p class="report-thesis">{{ focusReportCard ? t('report.focusThesis') : stageLabel }}</p>
          <div class="report-score-inline">
            <span v-if="sectionReady('total_score')" class="section-reveal">{{ displayReport.total_score }} / 5</span>
            <span v-else class="report-skeleton chip"></span>
            <span v-if="sectionReady('total_score')" class="section-reveal">{{ displayReport.total_score_30 }} / 30</span>
            <span v-else class="report-skeleton chip"></span>
            <span>{{ t('report.question', { number: session?.question_no }) }}</span>
          </div>
        </div>
        <div class="report-priority-card">
          <span class="action-kicker">{{ t('report.startHere') }}</span>
          <h2 v-if="focusReportCard" class="section-reveal">{{ focusReportCard.label }}</h2>
          <div v-else class="report-skeleton heading"></div>
          <p v-if="focusReportCard?.problem" class="section-reveal">{{ focusReportCard.problem }}</p>
          <div v-else class="skeleton-copy"><i></i><i></i><i class="short"></i></div>
          <div class="priority-next">
            <strong>{{ t('report.doNext') }}</strong>
            <p v-if="focusReportCard?.improvement" class="section-reveal">{{ focusReportCard.improvement }}</p>
            <div v-else class="skeleton-copy"><i></i><i class="short"></i></div>
          </div>
        </div>
      </header>

      <section class="report-snapshot slim">
        <div class="snapshot-card panel">
          <span>{{ t('report.totalScore') }}</span>
          <strong v-if="sectionReady('total_score')" class="section-reveal">{{ displayReport.total_score }} / 5</strong>
          <div v-else class="report-skeleton metric"></div>
          <p v-if="sectionReady('total_score')">{{ t('report.converted', { score: displayReport.total_score_30 }) }}</p>
          <div v-else class="report-skeleton line"></div>
        </div>
        <div class="snapshot-card panel">
          <span>{{ t('report.strongestArea') }}</span>
          <strong v-if="strongestReportCard" class="section-reveal">{{ strongestReportCard.label }}</strong>
          <div v-else class="report-skeleton metric wide"></div>
          <p v-if="strongestReportCard">{{ strongestReportCard.score }} / 5</p>
          <div v-else class="report-skeleton line"></div>
        </div>
        <div class="snapshot-card panel">
          <span>{{ t('report.languageFlags') }}</span>
          <strong v-if="sectionReady('grammar_analysis')" class="section-reveal">{{ grammarIssueCount + spellingIssueCount }}</strong>
          <div v-else class="report-skeleton metric"></div>
          <p v-if="sectionReady('grammar_analysis')">{{ t('report.flagSummary', { grammar: grammarIssueCount, spelling: spellingIssueCount }) }}</p>
          <div v-else class="report-skeleton line"></div>
        </div>
      </section>

      <section class="report-section">
        <div class="section-head compact-head">
          <div>
            <p class="eyebrow">{{ t('report.breakdown') }}</p>
            <h2 class="section-title">{{ t('report.scoreByCriteria') }}</h2>
          </div>
        </div>
        <div class="criteria-list">
          <article
            v-for="(card, index) in priorityActionCards"
            :key="card.key"
            class="criteria-row"
            :class="{ priority: index === 0 }"
          >
            <span class="criteria-rank">{{ String(index + 1).padStart(2, '0') }}</span>
            <div class="criteria-card-head">
              <h3>{{ card.label }}</h3>
              <strong v-if="card.score !== null" class="section-reveal">{{ card.score }} / 5</strong>
              <span v-else class="report-skeleton score"></span>
            </div>
            <div class="score-track" :class="{ loading: !sectionReady('scores') }"><span :style="{ width: `${card.percent}%` }"></span></div>
            <p v-if="card.problem" class="section-reveal">{{ card.problem }}</p>
            <div v-else class="skeleton-copy"><i></i><i></i><i class="short"></i></div>
          </article>
        </div>
      </section>

      <section class="report-section action-plan">
        <div class="action-plan-head">
          <p class="eyebrow">{{ t('report.actionPlan') }}</p>
          <h2 class="section-title">{{ t('report.actionPlanByCriteria') }}</h2>
        </div>
        <details
          v-for="(card, index) in priorityActionCards"
          :key="`priority-${card.key}`"
          class="priority-step"
          :class="{ primary: index === 0 }"
          :open="index === 0"
        >
          <summary>
            <span class="step-number">{{ index + 1 }}</span>
            <span><strong>{{ card.label }}</strong><small>{{ card.score }} / 5</small></span>
            <i aria-hidden="true"></i>
          </summary>
          <div class="priority-step-body">
            <div>
              <span class="action-kicker">{{ t('report.breakdown') }}</span>
              <p v-if="card.problem">{{ card.problem }}</p>
              <div v-else class="skeleton-copy"><i></i><i class="short"></i></div>
            </div>
            <div class="next-step-box">
              <span class="action-kicker">{{ t('report.nextStep') }}</span>
              <router-link v-if="card.key === 'linguistic_expression' && sectionReady('improvements')" class="grammar-next-link" :to="grammarAnalysisPath">{{ t('report.openGrammar') }}</router-link>
              <p v-if="card.improvement" class="section-reveal">{{ card.improvement }}</p>
              <div v-else class="skeleton-copy"><i></i><i></i><i class="short"></i></div>
            </div>
          </div>
        </details>
      </section>

      <section class="rewrite-entry">
        <div>
          <p class="eyebrow">{{ t('report.aiRewrite') }}</p>
          <h2>{{ t('rewrite.entryTitle') }}</h2>
          <p>{{ t('rewrite.entryBody') }}</p>
        </div>
        <router-link class="btn primary" :to="rewritePath">{{ t('rewrite.open') }}</router-link>
      </section>

      <section v-if="report && !isExampleSession && feedbackStatusLoaded" class="report-feedback-entry">
        <div>
          <MessageSquare :size="20" />
          <span><strong>{{ feedbackStatus.submitted ? t('report.feedback.submittedTitle') : t('report.feedback.title') }}</strong><small>{{ feedbackStatus.submitted ? t('report.feedback.submittedBody') : t('report.feedback.body') }}</small></span>
        </div>
        <button v-if="!feedbackStatus.submitted" class="btn" @click="openFeedback"><MessageSquare :size="16" />{{ t('report.feedback.open') }}</button>
      </section>
    </article>

    <n-modal v-model:show="feedbackOpen">
      <div class="panel report-feedback-dialog" role="dialog" aria-modal="true" aria-labelledby="report-feedback-title">
        <header><div><p class="eyebrow">{{ t('report.feedback.open') }}</p><h2 id="report-feedback-title">{{ t('report.feedback.dialogTitle') }}</h2><p>{{ t('report.feedback.dialogBody') }}</p></div><button class="btn ghost small icon-btn" :title="t('report.feedback.cancel')" :aria-label="t('report.feedback.cancel')" @click="feedbackOpen = false"><X :size="17" /></button></header>
        <div class="report-feedback-choices" role="radiogroup">
          <button type="button" :class="{ active: feedbackType === 'too_high' }" role="radio" :aria-checked="feedbackType === 'too_high'" @click="feedbackType = 'too_high'"><TrendingUp :size="19" /><span><strong>{{ t('report.feedback.tooHigh') }}</strong></span></button>
          <button type="button" :class="{ active: feedbackType === 'too_low' }" role="radio" :aria-checked="feedbackType === 'too_low'" @click="feedbackType = 'too_low'"><TrendingDown :size="19" /><span><strong>{{ t('report.feedback.tooLow') }}</strong></span></button>
          <button type="button" :class="{ active: feedbackType === 'other' }" role="radio" :aria-checked="feedbackType === 'other'" @click="feedbackType = 'other'"><CircleHelp :size="19" /><span><strong>{{ t('report.feedback.other') }}</strong></span></button>
        </div>
        <label class="form-field"><span>{{ t('report.feedback.comment') }}</span><textarea v-model="feedbackComment" class="textarea" maxlength="4000" :required="feedbackType === 'other'" :placeholder="t('report.feedback.commentPlaceholder')"></textarea></label>
        <label class="report-feedback-consent"><input v-model="feedbackConsent" type="checkbox" /><span>{{ t('report.feedback.consent') }}</span></label>
        <footer><button class="btn" type="button" @click="feedbackOpen = false">{{ t('report.feedback.cancel') }}</button><button class="btn primary" type="button" :disabled="!canSubmitFeedback || feedbackSubmitting" @click="submitFeedback">{{ feedbackSubmitting ? t('report.feedback.submitting') : t('report.feedback.submit') }}</button></footer>
      </div>
    </n-modal>

    <article v-if="active === 'rewrite'" class="rewrite-workspace">
      <header class="rewrite-heading">
        <div>
          <p class="eyebrow">{{ t('report.aiRewrite') }}</p>
          <h1>{{ t('rewrite.title') }}</h1>
          <p>{{ t('rewrite.subtitle') }}</p>
        </div>
      </header>

      <div v-if="!sectionReady('rewrite_comparison') && !report" class="grammar-evaluating panel panel-pad" aria-live="polite">
        <div class="evaluation-spinner" aria-hidden="true"><span></span></div>
        <div>
          <strong>{{ t('report.evaluating') }}</strong>
          <p>{{ stageLabel }}</p>
        </div>
        <div class="skeleton-copy"><i></i><i></i><i></i><i class="short"></i></div>
      </div>

      <section v-else class="rewrite-document panel" aria-label="AI rewrite comparison">
        <div class="rewrite-column-heads" aria-hidden="true">
          <strong>{{ t('rewrite.aiVersion') }}</strong>
          <strong>{{ t('rewrite.originalVersion') }}</strong>
        </div>
        <div class="rewrite-rows">
          <section v-for="(section, sectionIndex) in rewriteSections" :key="`${section.role}-${sectionIndex}`" class="rewrite-row">
            <h2>{{ t(`rewrite.roles.${section.role}`) }}</h2>
            <div class="rewrite-cell rewritten">
              <span class="rewrite-mobile-label">{{ t('rewrite.aiVersion') }}</span>
              <p>
                <template v-for="(part, index) in buildRewriteParts(section.rewritten_text, section.highlights, 'rewritten')" :key="index">
                  <mark v-if="part.type" class="semantic-highlight" :class="part.type">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
                </template>
              </p>
            </div>
            <div class="rewrite-cell original">
              <span class="rewrite-mobile-label">{{ t('rewrite.originalVersion') }}</span>
              <p>
                <template v-for="(part, index) in buildRewriteParts(section.original_text, section.highlights, 'original')" :key="index">
                  <mark v-if="part.type" class="semantic-highlight" :class="part.type">{{ part.text }}</mark><span v-else>{{ part.text }}</span>
                </template>
              </p>
            </div>
          </section>
        </div>
        <footer class="rewrite-legend">
          <strong>{{ t('rewrite.legendTitle') }}</strong>
          <span><i class="highlight-swatch logic_connector"></i>{{ t('rewrite.legend.logicConnector') }}</span>
          <span><i class="highlight-swatch logic_bridge"></i>{{ t('rewrite.legend.logicBridge') }}</span>
          <span><i class="highlight-swatch removed_content"></i>{{ t('rewrite.legend.removedContent') }}</span>
          <span><i class="highlight-swatch core_expression"></i>{{ t('rewrite.legend.coreExpression') }}</span>
        </footer>
      </section>
    </article>

    <article v-if="active === 'grammar'" class="legacy-report panel panel-pad">
      <h1 class="legacy-title">{{ t('report.grammarAnalysis') }}</h1>
      <p class="legacy-meta">{{ t('report.interactiveReport') }}</p>
      <div v-if="!sectionReady('grammar_analysis')" class="grammar-evaluating" aria-live="polite">
        <div class="evaluation-spinner" aria-hidden="true"><span></span></div>
        <div>
          <strong>{{ t('report.evaluating') }}</strong>
          <p>{{ stageLabel }}</p>
        </div>
        <div class="skeleton-copy"><i></i><i></i><i></i><i class="short"></i></div>
      </div>
      <template v-else>
      <div class="grammar-legend">
        <span><i class="legend-dot grammar"></i>Grammar</span>
        <span><i class="legend-dot spelling"></i>Spelling</span>
        <span><i class="legend-dot wording"></i>Wording</span>
      </div>

      <h3>{{ t('report.yourAnswer') }}</h3>
      <p class="annotated-essay" v-if="annotatedAnswer.length">
        <template v-for="(part, index) in annotatedAnswer" :key="index">
          <span
            v-if="part.issues"
            class="essay-mark"
            :class="part.types"
          >{{ part.text }}<span class="issue-dots" aria-hidden="true"><i v-for="type in part.types" :key="type" :class="type"></i></span><span class="issue-tooltip"><span v-for="(issue, issueIndex) in part.issues" :key="issueIndex" class="issue-detail"><strong>{{ issueLabel(issue.issue_type) }}</strong><span>Problem: {{ issue.explanation }}</span><span>Suggestion: {{ issue.suggestion }}</span></span></span></span><span v-else>{{ part.text }}</span>
        </template>
      </p>
      <p v-else class="annotated-essay muted">{{ t('report.noAnswer') }}</p>
      </template>
    </article>

    <section v-if="active === 'download'" class="panel panel-pad">
      <button v-if="report" class="btn primary" @click="downloadReport">{{ t('report.downloadReport') }}</button>
      <p v-else class="muted">{{ t('report.downloadWaiting') }}</p>
    </section>
  </AppShell>
</template>
