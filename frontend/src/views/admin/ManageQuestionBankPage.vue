<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { FilePlus2, Pencil, Search, Trash2, X } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import AdminShell from '../../components/AdminShell.vue'
import { apiDelete, apiGet, apiPatch, apiPost } from '../../api/client'
import type { AdminQuestion } from '../../types/questions'
import { questionMessage } from '../../types/questions'

const message = useMessage()
const rows = ref<AdminQuestion[]>([])
const topics = ref<string[]>([])
const loading = ref(true)
const submitting = ref(false)
const search = ref('')
const sourceFilter = ref<'all' | 'official' | 'user'>('all')
const statusFilter = ref<'all' | 'pending' | 'accepted' | 'rejected'>('all')
const editorOpen = ref(false)
const editing = ref<AdminQuestion | null>(null)
const deleteTarget = ref<AdminQuestion | null>(null)

const form = reactive({
  topic: '', exam_type: 'classic', difficulty: 'medium', summary: '', status: 'accepted',
  professor_name: '', professor_content: '', student_a_name: '', student_a_content: '',
  student_b_name: '', student_b_content: '', review_comment: ''
})

const filteredRows = computed(() => {
  const term = search.value.trim().toLowerCase()
  return rows.value.filter((row) => {
    if (sourceFilter.value !== 'all' && row.source !== sourceFilter.value) return false
    if (statusFilter.value !== 'all' && row.status !== statusFilter.value) return false
    return !term || `${row.question_no} ${row.summary} ${row.topic} ${row.creator_email ?? ''}`.toLowerCase().includes(term)
  })
})

function resetForm() {
  Object.assign(form, {
    topic: topics.value[0] ?? '', exam_type: 'classic', difficulty: 'medium', summary: '', status: 'accepted',
    professor_name: 'Dr. Diaz', professor_content: '', student_a_name: 'Claire', student_a_content: '',
    student_b_name: 'Andrew', student_b_content: '', review_comment: ''
  })
}

function openCreate() {
  editing.value = null
  resetForm()
  editorOpen.value = true
}

function openEdit(row: AdminQuestion) {
  editing.value = row
  const professor = questionMessage(row, 'professor')
  const studentA = questionMessage(row, 'student_a')
  const studentB = questionMessage(row, 'student_b')
  Object.assign(form, {
    topic: row.topic, exam_type: row.exam_type, difficulty: row.difficulty, summary: row.summary,
    status: row.status,
    professor_name: professor?.speaker_name ?? '', professor_content: professor?.content ?? '',
    student_a_name: studentA?.speaker_name ?? '', student_a_content: studentA?.content ?? '',
    student_b_name: studentB?.speaker_name ?? '', student_b_content: studentB?.content ?? '', review_comment: ''
  })
  editorOpen.value = true
}

async function loadQuestions() {
  loading.value = true
  try {
    ;[rows.value, topics.value] = await Promise.all([
      apiGet<AdminQuestion[]>('/admin/questions'),
      apiGet<string[]>('/questions/topics')
    ])
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to load questions')
  } finally {
    loading.value = false
  }
}

async function saveQuestion() {
  submitting.value = true
  try {
    const payload = { ...form }
    if (editing.value) {
      const updated = await apiPatch<AdminQuestion>(`/admin/questions/${editing.value.id}`, payload)
      rows.value = rows.value.map((row) => row.id === updated.id ? updated : row)
      message.success(`Question #${updated.question_no} updated`)
    } else {
      const created = await apiPost<AdminQuestion>('/admin/questions', payload)
      rows.value.unshift(created)
      message.success(`Official question #${created.question_no} created`)
    }
    editorOpen.value = false
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to save question')
  } finally {
    submitting.value = false
  }
}

async function deleteQuestion() {
  const target = deleteTarget.value
  if (!target) return
  submitting.value = true
  try {
    await apiDelete(`/admin/questions/${target.id}`)
    rows.value = rows.value.filter((row) => row.id !== target.id)
    message.success(`Question #${target.question_no} deleted`)
    deleteTarget.value = null
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to delete question')
  } finally {
    submitting.value = false
  }
}

onMounted(loadQuestions)
</script>

<template>
  <AdminShell>
    <header class="admin-page-head">
      <div><p class="eyebrow">Content operations</p><h1>Question bank</h1><p>Maintain official prompts and published or archived community submissions.</p></div>
      <button class="btn primary" @click="openCreate"><FilePlus2 :size="17" />Add official question</button>
    </header>

    <section class="admin-account-tools question-bank-tools">
      <label class="admin-search"><Search :size="16" /><input v-model="search" placeholder="Search number, prompt, topic, or uploader" /></label>
      <div class="admin-filter-group">
        <select v-model="sourceFilter" class="select"><option value="all">All sources</option><option value="official">Official</option><option value="user">User-created</option></select>
        <select v-model="statusFilter" class="select"><option value="all">All statuses</option><option value="accepted">Published</option><option value="pending">Pending</option><option value="rejected">Archived</option></select>
        <span>{{ filteredRows.length }} questions</span>
      </div>
    </section>

    <section class="panel admin-account-table-wrap">
      <table class="data-table admin-question-table question-bank-table">
        <thead><tr><th>No.</th><th>Prompt</th><th>Source</th><th>Status</th><th>Usage</th><th aria-label="Actions"></th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="muted">Loading question bank...</td></tr>
          <tr v-else-if="!filteredRows.length"><td colspan="6" class="admin-empty-row">No questions match these filters.</td></tr>
          <tr v-for="row in filteredRows" :key="row.id">
            <td><strong>#{{ row.question_no }}</strong></td>
            <td class="admin-question-summary"><strong>{{ row.summary }}</strong><small>{{ row.topic }} · {{ row.exam_type === 'reform_2026' ? '26 Reform' : 'Common' }} · {{ row.difficulty }}</small><small class="question-mobile-meta">{{ row.source === 'user' ? 'User-created' : 'Official' }} · {{ row.status === 'accepted' ? 'Published' : row.status === 'rejected' ? 'Archived' : 'Pending' }}</small></td>
            <td><span class="admin-source" :class="row.source">{{ row.source === 'user' ? 'User-created' : 'Official' }}</span><small v-if="row.creator_alias" class="table-secondary">{{ row.creator_alias }}</small></td>
            <td><span class="admin-status" :class="row.status">{{ row.status === 'accepted' ? 'published' : row.status === 'rejected' ? 'archived' : row.status }}</span></td>
            <td>{{ row.session_count }} sessions</td>
            <td><div class="admin-row-actions"><button class="btn ghost small icon-btn" title="Edit question" aria-label="Edit question" @click="openEdit(row)"><Pencil :size="15" /></button><button class="btn danger small icon-btn" :disabled="row.session_count > 0" :title="row.session_count ? 'Archive questions with existing sessions' : 'Delete question'" aria-label="Delete question" @click="deleteTarget = row"><Trash2 :size="15" /></button></div></td>
          </tr>
        </tbody>
      </table>
    </section>

    <n-modal v-model:show="editorOpen">
      <div class="panel admin-dialog question-editor-dialog" role="dialog" aria-modal="true" aria-labelledby="question-editor-title">
        <header><div><p class="eyebrow">{{ editing ? `${editing.source} question #${editing.question_no}` : 'Official question' }}</p><h2 id="question-editor-title">{{ editing ? 'Edit question' : 'Add official question' }}</h2></div><button class="btn ghost small icon-btn" title="Close" aria-label="Close" @click="editorOpen = false"><X :size="17" /></button></header>
        <form @submit.prevent="saveQuestion">
          <div class="question-editor-meta">
            <label class="form-field">Topic<select v-model="form.topic" class="select" required><option v-for="topic in topics" :key="topic">{{ topic }}</option></select></label>
            <label class="form-field">Format<select v-model="form.exam_type" class="select"><option value="classic">Common</option><option value="reform_2026">26 Reform</option></select></label>
            <label class="form-field">Difficulty<select v-model="form.difficulty" class="select"><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
            <label class="form-field">Status<select v-model="form.status" class="select"><option v-if="editing?.status === 'pending'" value="pending">Pending review</option><option value="accepted">Published</option><option value="rejected">Archived</option></select></label>
          </div>
          <label class="form-field">Question summary<input v-model="form.summary" class="input" minlength="3" maxlength="240" required /></label>
          <div class="question-editor-block"><strong>Professor prompt</strong><div class="form-grid compact"><label class="form-field">Name<input v-model="form.professor_name" class="input" maxlength="120" required /></label><label class="form-field wide">Content<textarea v-model="form.professor_content" class="textarea" minlength="20" maxlength="5000" required></textarea></label></div></div>
          <div class="question-editor-block"><strong>Student perspectives</strong><div class="form-grid"><div><label class="form-field">Student A name<input v-model="form.student_a_name" class="input" maxlength="120" required /></label><label class="form-field">Student A content<textarea v-model="form.student_a_content" class="textarea" minlength="10" maxlength="5000" required></textarea></label></div><div><label class="form-field">Student B name<input v-model="form.student_b_name" class="input" maxlength="120" required /></label><label class="form-field">Student B content<textarea v-model="form.student_b_content" class="textarea" minlength="10" maxlength="5000" required></textarea></label></div></div></div>
          <label v-if="editing?.source === 'user' && form.status !== editing.status" class="form-field">Status-change note<textarea v-model="form.review_comment" class="textarea compact-textarea" maxlength="2000" :required="form.status === 'rejected'" placeholder="This note is sent to the uploader."></textarea></label>
          <footer><button class="btn" type="button" @click="editorOpen = false">Cancel</button><button class="btn primary" type="submit" :disabled="submitting">{{ editing ? 'Save changes' : 'Create official question' }}</button></footer>
        </form>
      </div>
    </n-modal>

    <n-modal :show="Boolean(deleteTarget)" @update:show="(show: boolean) => { if (!show) deleteTarget = null }">
      <div class="panel admin-dialog danger-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-question-title">
        <header><div><p class="eyebrow">Permanent action</p><h2 id="delete-question-title">Delete question #{{ deleteTarget?.question_no }}</h2></div><button class="btn ghost small icon-btn" title="Close" aria-label="Close" @click="deleteTarget = null"><X :size="17" /></button></header>
        <p>This removes the prompt and its moderation record. Questions with answer sessions must be archived instead.</p>
        <footer><button class="btn" @click="deleteTarget = null">Cancel</button><button class="btn danger" :disabled="submitting" @click="deleteQuestion"><Trash2 :size="16" />Delete permanently</button></footer>
      </div>
    </n-modal>
  </AdminShell>
</template>
