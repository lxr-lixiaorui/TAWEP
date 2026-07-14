<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { CheckCircle2, Send } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPost } from '../api/client'

const message = useMessage()
const topics = ref<string[]>([])
const submitting = ref(false)
const submittedNumber = ref<number | null>(null)
const form = reactive({ topic: '', exam_type: 'classic', difficulty: 'medium', student_a_name: '', student_a_content: '', student_b_name: '', student_b_content: '', professor_name: '', professor_content: '' })

async function submit() {
  submitting.value = true
  try {
    const result = await apiPost<{ question_no: number }>('/questions/upload', form)
    submittedNumber.value = result.question_no
    message.success('Question submitted for review')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to submit question')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => { topics.value = await apiGet('/questions/topics'); form.topic = topics.value[0] || '' })
</script>

<template>
  <AppShell>
    <header class="submission-head">
      <p class="eyebrow">Community question bank</p>
      <h1 class="simple-title">Create your own discussion prompt</h1>
      <p>Submit a complete Academic Discussion prompt. It will become available after administrator review.</p>
    </header>
    <section v-if="submittedNumber" class="panel submission-success">
      <CheckCircle2 :size="28" />
      <div><strong>Question #{{ submittedNumber }} is awaiting review</strong><p>You will receive an inbox message after an administrator makes a decision.</p></div>
      <router-link class="btn" to="/questionbank">Return to question bank</router-link>
    </section>
    <form v-else class="panel panel-pad submission-form" @submit.prevent="submit">
      <div class="form-grid submission-meta-grid">
        <label class="form-field">Topic<select v-model="form.topic" class="select"><option v-for="topic in topics" :key="topic" :value="topic">{{ topic }}</option></select></label>
        <label class="form-field">Exam format<select v-model="form.exam_type" class="select"><option value="classic">Common format</option><option value="reform_2026">26 Reform</option></select></label>
        <label class="form-field">Difficulty<select v-model="form.difficulty" class="select"><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
      </div>
      <div class="submission-section"><span>01</span><div><strong>Professor prompt</strong><small>Include the discussion context and the question students must answer.</small></div></div>
      <label class="form-field">Professor name<input v-model="form.professor_name" class="input" maxlength="120" required /></label>
      <label class="form-field">Professor content<textarea v-model="form.professor_content" class="textarea" minlength="20" maxlength="5000" required></textarea></label>
      <div class="submission-section"><span>02</span><div><strong>Student perspectives</strong><small>Add two distinct viewpoints that a test taker can respond to.</small></div></div>
      <div class="form-grid">
        <label class="form-field">Student A name<input v-model="form.student_a_name" class="input" maxlength="120" required /></label>
        <label class="form-field">Student B name<input v-model="form.student_b_name" class="input" maxlength="120" required /></label>
      </div>
      <div class="form-grid">
        <label class="form-field">Student A content<textarea v-model="form.student_a_content" class="textarea" minlength="10" maxlength="5000" required></textarea></label>
        <label class="form-field">Student B content<textarea v-model="form.student_b_content" class="textarea" minlength="10" maxlength="5000" required></textarea></label>
      </div>
      <footer class="submission-actions"><span>All submissions are reviewed before publication.</span><button class="btn primary" type="submit" :disabled="submitting"><Send :size="16" />{{ submitting ? 'Submitting...' : 'Submit for review' }}</button></footer>
    </form>
  </AppShell>
</template>
