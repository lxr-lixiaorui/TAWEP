<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Check, Eye, RefreshCw, X, XCircle } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import AdminShell from '../../components/AdminShell.vue'
import { apiGet, apiPost } from '../../api/client'
import type { QuestionReview } from '../../types/questions'
import { questionMessage } from '../../types/questions'

const message = useMessage()
const rows = ref<QuestionReview[]>([])
const loading = ref(false)
const submitting = ref(false)
const statusFilter = ref<'pending' | 'accepted' | 'rejected'>('pending')
const selected = ref<QuestionReview | null>(null)
const comment = ref('')

async function loadReviews() {
  loading.value = true
  try {
    rows.value = await apiGet<QuestionReview[]>(`/admin/review-questions?status=${statusFilter.value}`)
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to load review queue')
  } finally {
    loading.value = false
  }
}

function openReview(row: QuestionReview) {
  selected.value = row
  comment.value = row.comment ?? ''
}

async function decide(action: 'accept' | 'reject') {
  if (!selected.value) return
  submitting.value = true
  try {
    await apiPost(`/admin/review-questions/${selected.value.question.id}/${action}`, { comment: comment.value || null })
    message.success(`Question ${action === 'accept' ? 'accepted' : 'rejected'}`)
    selected.value = null
    await loadReviews()
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to save decision')
  } finally {
    submitting.value = false
  }
}

async function setStatus(value: 'pending' | 'accepted' | 'rejected') {
  statusFilter.value = value
  await loadReviews()
}

onMounted(loadReviews)
</script>

<template>
  <AdminShell>
    <header class="admin-page-head">
      <div><p class="eyebrow">Moderation</p><h1>Review uploads</h1><p>Inspect the complete discussion before publishing it to the practice bank.</p></div>
      <button class="btn" :disabled="loading" @click="loadReviews"><RefreshCw :size="16" />Refresh</button>
    </header>

    <section class="admin-review-toolbar">
      <div class="admin-segmented" aria-label="Review status">
        <button :class="{ active: statusFilter === 'pending' }" @click="setStatus('pending')">Pending</button>
        <button :class="{ active: statusFilter === 'accepted' }" @click="setStatus('accepted')">Accepted</button>
        <button :class="{ active: statusFilter === 'rejected' }" @click="setStatus('rejected')">Rejected</button>
      </div>
      <span>{{ rows.length }} {{ statusFilter }} submissions</span>
    </section>

    <section class="panel admin-account-table-wrap">
      <table class="data-table admin-question-table">
        <thead><tr><th>No.</th><th>Prompt</th><th>Uploader</th><th>Format</th><th>Submitted</th><th aria-label="Action"></th></tr></thead>
        <tbody>
          <tr v-if="loading"><td colspan="6" class="muted">Loading review queue...</td></tr>
          <tr v-else-if="!rows.length"><td colspan="6" class="admin-empty-row"><Check :size="19" />No {{ statusFilter }} uploads.</td></tr>
          <tr v-for="row in rows" :key="row.review_id">
            <td><strong>#{{ row.question.question_no }}</strong></td>
            <td class="admin-question-summary"><strong>{{ row.question.summary }}</strong><small>{{ row.question.topic }} · {{ row.question.difficulty }}</small></td>
            <td><strong>{{ row.question.creator_alias || 'Deleted user' }}</strong><small class="table-secondary">{{ row.question.creator_email }}</small></td>
            <td>{{ row.question.exam_type === 'reform_2026' ? '26 Reform' : 'Common' }}</td>
            <td>{{ new Date(row.question.created_at).toLocaleDateString() }}</td>
            <td><button class="btn ghost small" @click="openReview(row)"><Eye :size="15" />Review</button></td>
          </tr>
        </tbody>
      </table>
    </section>

    <n-modal :show="Boolean(selected)" @update:show="(show: boolean) => { if (!show) selected = null }">
      <div v-if="selected" class="panel admin-dialog question-review-dialog" role="dialog" aria-modal="true" aria-labelledby="review-question-title">
        <header><div><p class="eyebrow">Question #{{ selected.question.question_no }} · {{ selected.question.source }}</p><h2 id="review-question-title">{{ selected.question.summary }}</h2></div><button class="btn ghost small icon-btn" title="Close" aria-label="Close" @click="selected = null"><X :size="17" /></button></header>
        <div class="question-review-meta">
          <span><small>Uploader</small><strong>{{ selected.question.creator_alias || 'Deleted user' }}</strong><em>{{ selected.question.creator_email }}</em></span>
          <span><small>Topic</small><strong>{{ selected.question.topic }}</strong></span>
          <span><small>Format</small><strong>{{ selected.question.exam_type === 'reform_2026' ? '26 Reform' : 'Common' }}</strong></span>
          <span><small>Difficulty</small><strong>{{ selected.question.difficulty }}</strong></span>
          <span><small>Words</small><strong>{{ selected.question.word_count }}</strong></span>
        </div>
        <div class="question-transcript">
          <article v-for="role in (['professor', 'student_a', 'student_b'] as const)" :key="role" :class="role">
            <span>{{ role === 'professor' ? 'Prompt' : 'Perspective' }}</span>
            <h3>{{ questionMessage(selected.question, role)?.speaker_name }}</h3>
            <p>{{ questionMessage(selected.question, role)?.content }}</p>
          </article>
        </div>
        <label class="form-field"><span>{{ selected.status === 'pending' ? 'Reviewer note' : 'Decision note' }}</span><textarea v-model="comment" class="textarea" maxlength="2000" :readonly="selected.status !== 'pending'" placeholder="Required when rejecting; optional when accepting."></textarea></label>
        <footer v-if="selected.status === 'pending'">
          <button class="btn danger" :disabled="submitting || !comment" @click="decide('reject')"><XCircle :size="16" />Reject</button>
          <button class="btn primary" :disabled="submitting" @click="decide('accept')"><Check :size="16" />Accept and publish</button>
        </footer>
        <footer v-else><span class="admin-status" :class="selected.status">{{ selected.status }}</span><button class="btn" @click="selected = null">Close</button></footer>
      </div>
    </n-modal>
  </AdminShell>
</template>
