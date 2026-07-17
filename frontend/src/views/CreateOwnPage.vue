<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { CheckCircle2, Send } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPost } from '../api/client'
import { useAppStore } from '../stores/app'

const message = useMessage()
const app = useAppStore()
const topics = ref<string[]>([])
const submitting = ref(false)
const submittedNumber = ref<number | null>(null)
const form = reactive({
  topic: '', exam_type: '', difficulty: 'medium', student_a_name: '', student_a_content: '',
  student_b_name: '', student_b_content: '', professor_name: '', professor_content: '',
  rights_confirmed: false, rights_statement_version: '2026-07-16'
})
const copy = computed(() => app.locale === 'zh' ? {
  eyebrow: '社区题库', title: '创建学术讨论题目', subtitle: '提交完整题目，管理员审核通过后才会在题库中公开。',
  awaiting: '正在等待审核', inbox: '管理员完成审核后，你会在收件箱收到通知。', back: '返回题库',
  topic: '话题', format: '考试格式', common: '通用经典题', reform: '26 改革题', difficulty: '难度',
  easy: '简单', medium: '中等', hard: '困难', professorPrompt: '教授题干', professorHelp: '填写讨论背景以及考生需要回答的核心问题。',
  professorName: '教授姓名', professorContent: '教授内容', perspectives: '学生观点', perspectiveHelp: '加入两个不同观点，供考生回应和拓展。',
  studentAName: '学生 A 姓名', studentBName: '学生 B 姓名', studentAContent: '学生 A 内容', studentBContent: '学生 B 内容',
  rights: '我确认拥有题目所需的合法权利，并同意平台审核和公开展示。我对题目来源负责，不得上传违反 ETS 或其他机构条款、版权、商标、保密或考试安全规则的材料。',
  reviewed: '所有题目在公开前都会经过审核。', submit: '提交审核', submitting: '正在提交…', success: '题目已提交审核', failure: '无法提交题目'
} : {
  eyebrow: 'Community question bank', title: 'Create an Academic Discussion prompt', subtitle: 'Submit a complete prompt. It becomes public only after administrator approval.',
  awaiting: 'is awaiting review', inbox: 'You will receive an inbox message after an administrator makes a decision.', back: 'Return to question bank',
  topic: 'Topic', format: 'Exam format', common: 'Classic', reform: '26 Reform', difficulty: 'Difficulty',
  easy: 'Easy', medium: 'Medium', hard: 'Hard', professorPrompt: 'Professor prompt', professorHelp: 'Include the discussion context and the question students must answer.',
  professorName: 'Professor name', professorContent: 'Professor content', perspectives: 'Student perspectives', perspectiveHelp: 'Add two distinct viewpoints that a test taker can respond to.',
  studentAName: 'Student A name', studentBName: 'Student B name', studentAContent: 'Student A content', studentBContent: 'Student B content',
  rights: 'I confirm that I hold the necessary rights and authorize review and public display. I am responsible for the source and will not submit material that violates ETS or another institution’s terms, copyright, trademarks, confidentiality, or test-security rules.',
  reviewed: 'All submissions are reviewed before publication.', submit: 'Submit for review', submitting: 'Submitting...', success: 'Question submitted for review', failure: 'Unable to submit question'
})

async function submit() {
  submitting.value = true
  try {
    const result = await apiPost<{ question_no: number }>('/questions/upload', form)
    submittedNumber.value = result.question_no
    message.success(copy.value.success)
  } catch (error) {
    message.error(error instanceof Error ? error.message : copy.value.failure)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => { topics.value = await apiGet('/questions/topics'); form.topic = topics.value[0] || '' })
</script>

<template>
  <AppShell>
    <header class="submission-head">
      <p class="eyebrow">{{ copy.eyebrow }}</p><h1 class="simple-title">{{ copy.title }}</h1><p>{{ copy.subtitle }}</p>
    </header>
    <section v-if="submittedNumber" class="panel submission-success">
      <CheckCircle2 :size="28" />
      <div><strong>Question #{{ submittedNumber }} {{ copy.awaiting }}</strong><p>{{ copy.inbox }}</p></div>
      <router-link class="btn" to="/questionbank">{{ copy.back }}</router-link>
    </section>
    <form v-else class="panel panel-pad submission-form" @submit.prevent="submit">
      <div class="form-grid submission-meta-grid">
        <label class="form-field"><span>{{ copy.topic }}</span><select v-model="form.topic" class="select"><option v-for="topic in topics" :key="topic" :value="topic">{{ topic }}</option></select></label>
        <label class="form-field"><span>{{ copy.format }}</span><select v-model="form.exam_type" class="select" required><option disabled value="">{{ app.locale === 'zh' ? '请选择考试格式' : 'Select exam format' }}</option><option value="classic">{{ copy.common }}</option><option value="reform_2026">{{ copy.reform }}</option></select></label>
        <label class="form-field"><span>{{ copy.difficulty }}</span><select v-model="form.difficulty" class="select"><option value="easy">{{ copy.easy }}</option><option value="medium">{{ copy.medium }}</option><option value="hard">{{ copy.hard }}</option></select></label>
      </div>
      <div class="submission-section"><span>01</span><div><strong>{{ copy.professorPrompt }}</strong><small>{{ copy.professorHelp }}</small></div></div>
      <label class="form-field"><span>{{ copy.professorName }}</span><input v-model="form.professor_name" class="input" maxlength="120" required /></label>
      <label class="form-field"><span>{{ copy.professorContent }}</span><textarea v-model="form.professor_content" class="textarea" minlength="20" maxlength="5000" required></textarea></label>
      <div class="submission-section"><span>02</span><div><strong>{{ copy.perspectives }}</strong><small>{{ copy.perspectiveHelp }}</small></div></div>
      <div class="form-grid">
        <label class="form-field"><span>{{ copy.studentAName }}</span><input v-model="form.student_a_name" class="input" maxlength="120" required /></label>
        <label class="form-field"><span>{{ copy.studentBName }}</span><input v-model="form.student_b_name" class="input" maxlength="120" required /></label>
      </div>
      <div class="form-grid">
        <label class="form-field"><span>{{ copy.studentAContent }}</span><textarea v-model="form.student_a_content" class="textarea" minlength="10" maxlength="5000" required></textarea></label>
        <label class="form-field"><span>{{ copy.studentBContent }}</span><textarea v-model="form.student_b_content" class="textarea" minlength="10" maxlength="5000" required></textarea></label>
      </div>
      <label class="consent-row submission-consent">
        <input v-model="form.rights_confirmed" type="checkbox" required />
        <span><router-link to="/agreements/question-publication" target="_blank">{{ copy.rights }}</router-link></span>
      </label>
      <footer class="submission-actions"><span>{{ copy.reviewed }}</span><button class="btn primary" type="submit" :disabled="submitting"><Send :size="16" />{{ submitting ? copy.submitting : copy.submit }}</button></footer>
    </form>
  </AppShell>
</template>
