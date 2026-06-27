<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useMessage, useNotification } from 'naive-ui'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPatch, apiPost } from '../api/client'

const props = defineProps<{ activeTab?: string }>()
const route = useRoute()
const router = useRouter()
const message = useMessage()
const notification = useNotification()
const sessionId = String(route.params.sessionId)
const active = ref(props.activeTab || 'answer')
const session = ref<any | null>(null)
const report = ref<any | null>(null)
const grammar = ref<any[]>([])
const answer = ref('')
const downloadUrl = `/api/v1/sessions/${sessionId}/download`

async function saveDraft() {
  session.value = await apiPatch(`/sessions/${sessionId}/answer`, { answer_text: answer.value })
  message.success('Draft saved')
}

async function submit() {
  try {
    report.value = await apiPost(`/sessions/${sessionId}/submit`, { answer_text: answer.value })
    grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
    active.value = 'report'
    await router.replace(`/${sessionId}/report`)
  } catch {
    notification.error({ title: 'Credit is not enough', content: 'Each evaluation costs 3 credits.' })
  }
}

onMounted(async () => {
  session.value = await apiGet(`/sessions/${sessionId}`)
  answer.value = session.value.answer_text || ''
  if (active.value !== 'answer') {
    report.value = await apiGet(`/sessions/${sessionId}/report`)
    grammar.value = await apiGet(`/sessions/${sessionId}/grammar-analysis`)
  }
})
</script>

<template>
  <AppShell>
    <nav class="tabs">
      <button class="tab-btn" :class="{ active: active === 'answer' }" @click="active = 'answer'">Answer Page</button>
      <button class="tab-btn" :class="{ active: active === 'report' }" @click="active = 'report'">Report</button>
      <button class="tab-btn" :class="{ active: active === 'grammar' }" @click="active = 'grammar'">Grammar Analysis</button>
      <button class="tab-btn" :class="{ active: active === 'download' }" @click="active = 'download'">Download</button>
    </nav>

    <section v-if="active === 'answer'" class="content-grid">
      <textarea v-model="answer" class="textarea" style="min-height: 520px" placeholder="Write your academic discussion response here..."></textarea>
      <aside class="panel panel-pad">
        <h3>Session</h3><p class="muted">Mode: {{ session?.mode }}</p><p class="muted">Time limit: {{ session?.time_limit_seconds || 'Unlimited' }}</p>
        <div class="hero-actions"><button class="btn" @click="saveDraft">Save Draft</button><button class="btn primary" @click="submit">Submit for Evaluation</button></div>
      </aside>
    </section>

    <section v-if="active === 'report' && report" class="panel panel-pad">
      <h1 class="simple-title">{{ report.total_score }} / {{ report.total_score_30 }}</h1>
      <table class="data-table"><tbody>
        <tr><th>Content Relevance</th><td>{{ report.components.content_relevance }}</td><th>Perspective Expansion</th><td>{{ report.components.perspective_expansion }}</td></tr>
        <tr><th>Linguistic Expression</th><td>{{ report.components.linguistic_expression }}</td><th>Logical Structure</th><td>{{ report.components.logical_structure }}</td></tr>
      </tbody></table>
      <h3>AI Rewrite</h3><p>{{ report.ai_rewrite }}</p>
    </section>

    <section v-if="active === 'grammar'" class="panel">
      <table class="data-table"><thead><tr><th>#</th><th>Original</th><th>Type</th><th>Suggestion</th></tr></thead><tbody>
        <tr v-for="row in grammar" :key="row.sentence_index"><td>{{ row.sentence_index }}</td><td>{{ row.original_text }}</td><td>{{ row.issue_type }}</td><td>{{ row.suggestion }}</td></tr>
      </tbody></table>
    </section>

    <section v-if="active === 'download'" class="panel panel-pad"><a :href="downloadUrl" target="_blank" class="btn primary">Download HTML Report</a></section>
  </AppShell>
</template>
