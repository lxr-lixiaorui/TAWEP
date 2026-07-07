<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useMessage, useNotification } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPost } from '../api/client'

const props = defineProps<{ activeTab?: string }>()
const route = useRoute()
const router = useRouter()
const message = useMessage()
const notification = useNotification()
const sessionId = String(route.params.sessionId)
const active = ref(props.activeTab || 'answer')
const session = ref<any | null>(null)
const question = ref<any | null>(null)
const report = ref<any | null>(null)
const grammar = ref<any[]>([])
const answer = ref('')
const submittedAnswer = ref('')
const submitting = ref(false)
const timeLeft = ref<number | null>(null)
const hideTimer = ref(false)
const hideWordCount = ref(false)
const answerInput = ref<HTMLTextAreaElement | null>(null)
let timerId: number | undefined
const downloadUrl = `/api/v1/sessions/${sessionId}/download`

const wordCount = computed(() => answer.value.trim().split(/\s+/).filter(Boolean).length)
const timerLabel = computed(() => {
  if (timeLeft.value === null) return 'Unlimited'
  const minutes = Math.floor(timeLeft.value / 60)
  const seconds = timeLeft.value % 60
  return `00:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})
const timerUrgent = computed(() => timeLeft.value !== null && timeLeft.value <= 300)
const topActionLabel = computed(() => {
  if (submitting.value) return 'Evaluating...'
  return report.value ? 'Report' : 'Submit'
})
const orderedMessages = computed(() => [...(question.value?.messages ?? [])].sort((a, b) => a.sort_order - b.sort_order))
const professorMessage = computed(() => orderedMessages.value.find(item => item.speaker_role === 'professor') ?? orderedMessages.value[0])
const studentMessages = computed(() => orderedMessages.value.filter(item => item.speaker_role !== 'professor'))
const reportRows = computed(() => {
  if (!report.value) return []
  return [
    ['Content Relevance', report.value.components.content_relevance, 'content_relevance'],
    ['Perspectives Expansion', report.value.components.perspective_expansion, 'perspective_expansion'],
    ['Linguistic Expression', report.value.components.linguistic_expression, 'linguistic_expression'],
    ['Logical structure', report.value.components.logical_structure, 'logical_structure']
  ]
})
const grammarIssueCount = computed(() => grammar.value.filter(item => item.issue_type === 'grammar').length)
const answerForAnalysis = computed(() => submittedAnswer.value || answer.value || session.value?.answer_text || grammar.value.map(item => item.original_text).filter(Boolean).join(' '))
const spellingIssueCount = computed(() => grammar.value.filter(item => item.issue_type === 'spelling').length)
const annotatedAnswer = computed(() => buildAnnotatedAnswer(answerForAnalysis.value, grammar.value))

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
  if (submitting.value || report.value) return
  submittedAnswer.value = answer.value
  submitting.value = true
  try {
    report.value = await apiPost(`/sessions/${sessionId}/submit`, { answer_text: answer.value })
    grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
    stopTimer()
    message.success('Report is ready')
  } catch {
    notification.error({ title: 'Credit is not enough', content: 'Each evaluation costs 3 credits.' })
  } finally {
    submitting.value = false
  }
}

async function handleTopAction() {
  if (report.value) {
    active.value = 'report'
    await router.replace(`/${sessionId}/report`)
    return
  }
  await submit()
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
    grammar: 'Grammar issue',
    spelling: 'Spelling issue',
    wording: 'Wording issue'
  }[type] || 'Language issue'
}

function issueClass(type: string) {
  return ['grammar', 'spelling', 'wording'].includes(type) ? type : 'wording'
}

function buildAnnotatedAnswer(text: string, issues: any[]) {
  if (!text) return []
  const ranges: any[] = []
  let cursor = 0
  issues.forEach((issue) => {
    const rawNeedle = String(issue.original_text || '').trim()
    if (!rawNeedle) return
    const candidates = [rawNeedle, ...rawNeedle.split(/\s+/).filter(word => word.length > 3)]
    let start = -1
    let matched = ''
    for (const candidate of candidates) {
      start = text.indexOf(candidate, cursor)
      if (start === -1) start = text.indexOf(candidate)
      if (start !== -1) {
        matched = candidate
        break
      }
    }
    if (start === -1 || !matched) return
    const end = start + matched.length
    const overlaps = ranges.some(range => start < range.end && end > range.start)
    if (!overlaps) {
      ranges.push({ start, end, issue })
      cursor = end
    }
  })
  ranges.sort((a, b) => a.start - b.start)
  const parts: any[] = []
  let position = 0
  ranges.forEach((range) => {
    if (range.start > position) parts.push({ text: text.slice(position, range.start) })
    parts.push({ text: text.slice(range.start, range.end), issue: range.issue })
    position = range.end
  })
  if (position < text.length) parts.push({ text: text.slice(position) })
  return parts
}

onMounted(async () => {
  session.value = await apiGet(`/sessions/${sessionId}`)
  question.value = await apiGet(`/questions/${session.value.question_no}`)
  answer.value = session.value.answer_text || ''
  submittedAnswer.value = answer.value
  if (active.value !== 'answer') {
    report.value = await apiGet(`/sessions/${sessionId}/report`)
    grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
    stopTimer()
  } else {
    startTimer()
  }
})

onUnmounted(() => {
  if (timerId) window.clearInterval(timerId)
})

watch(active, async (next) => {
  if (next !== 'answer') stopTimer()
  if (next === 'report' && !report.value) {
    report.value = await apiGet(`/sessions/${sessionId}/report`)
  }
  if (next === 'grammar' && grammar.value.length === 0) {
    grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
  }
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
      <button class="tab-btn" :class="{ active: active === 'answer' }" @click="active = 'answer'">Answer Page</button>
      <button class="tab-btn" :class="{ active: active === 'report' }" @click="active = 'report'">Report</button>
      <button class="tab-btn" :class="{ active: active === 'grammar' }" @click="active = 'grammar'">Grammar Analysis</button>
      <button class="tab-btn" :class="{ active: active === 'download' }" @click="active = 'download'">Download</button>
    </nav>

    <article v-if="active === 'report' && report" class="legacy-report panel panel-pad">
      <p class="muted">Deepseek Evaluation Report</p>
      <h1 class="legacy-title">TAWEP Evaluation Report</h1>
      <p class="legacy-meta">Question: {{ session?.question_no }} · Session: {{ sessionId }}</p>

      <h3>&gt; Total Score(5/30):</h3>
      <div class="legacy-score">{{ report.total_score }} / {{ report.total_score_30 }}</div>

      <h3>&gt; Breakdown</h3>
      <div class="legacy-breakdown">
        <div class="legacy-cell muted">Criteria</div>
        <div class="legacy-cell muted">Score</div>
        <template v-for="row in reportRows" :key="row[2]">
          <div class="legacy-cell">{{ row[0] }}</div>
          <div class="legacy-cell">{{ row[1] }}</div>
        </template>
      </div>

      <div class="legacy-counts">
        <div>
          <p>Spelling mistakes count:</p>
          <strong class="orange">{{ spellingIssueCount }}</strong>
        </div>
        <div>
          <p>Grammar mistakes count:</p>
          <strong class="green">{{ grammarIssueCount }}</strong>
        </div>
      </div>

      <h3>&gt; Problem Analysis</h3>
      <p v-for="row in reportRows" :key="`problem-${row[2]}`">- {{ row[0] }}: {{ report.problems[row[2] as string] }}</p>

      <h3>&gt; Improvements</h3>
      <p v-for="row in reportRows" :key="`improvement-${row[2]}`">- {{ row[0] }}: {{ report.improvements[row[2] as string] }}</p>

      <h3>&gt; AI Rewrite</h3>
      <p>{{ report.ai_rewrite }}</p>
    </article>

    <article v-if="active === 'grammar'" class="legacy-report panel panel-pad">
      <h1 class="legacy-title">Grammar Analysis</h1>
      <p class="legacy-meta">Interactive language report</p>
      <div class="grammar-legend">
        <span><i class="legend-dot grammar"></i>Grammar</span>
        <span><i class="legend-dot spelling"></i>Spelling</span>
        <span><i class="legend-dot wording"></i>Wording</span>
      </div>

      <h3>&gt; Your Answer</h3>
      <p class="annotated-essay" v-if="annotatedAnswer.length">
        <template v-for="(part, index) in annotatedAnswer" :key="index">
          <span
            v-if="part.issue"
            class="essay-mark"
            :class="issueClass(part.issue.issue_type)"
          >{{ part.text }}<span class="issue-tooltip"><strong>{{ issueLabel(part.issue.issue_type) }}</strong><span>Problem: {{ part.issue.explanation }}</span><span>Suggestion: {{ part.issue.suggestion }}</span></span></span><span v-else>{{ part.text }}</span>
        </template>
      </p>
      <p v-else class="annotated-essay muted">No answer text was submitted.</p>
    </article>

    <section v-if="active === 'download'" class="panel panel-pad"><a :href="downloadUrl" target="_blank" class="btn primary">Download HTML Report</a></section>
  </AppShell>
</template>


