<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { apiGet } from '../api/client'

const filters = reactive({ difficulty: '', source: '', topic: '' })
const questions = ref<any[]>([])
const topics = ref<string[]>([])

async function loadQuestions() {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value)
  })
  questions.value = await apiGet(`/questions${params.toString() ? `?${params.toString()}` : ''}`)
}

onMounted(async () => {
  topics.value = await apiGet('/questions/topics')
  await loadQuestions()
})
</script>

<template>
  <AppShell>
    <div class="page-title">
      <div>
        <h1>We provide 100+ questions, or upload your own.</h1>
        <p class="muted">Filter by difficulty, source, and topic. Prompts are automatically grouped by topic for TOEFL Academic Discussion practice.</p>
      </div>
      <router-link to="/createyourown" class="btn primary">Upload your own</router-link>
    </div>

    <div class="panel toolbar">
      <div class="control-row">
        <select v-model="filters.difficulty" class="select" @change="loadQuestions">
          <option value="">Difficulty</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option>
        </select>
        <select v-model="filters.source" class="select" @change="loadQuestions">
          <option value="">Source</option><option value="official">Official</option><option value="user">User created</option>
        </select>
        <select v-model="filters.topic" class="select" @change="loadQuestions">
          <option value="">Topic</option><option v-for="topic in topics" :key="topic" :value="topic">{{ topic }}</option>
        </select>
      </div>
    </div>

    <div class="panel" style="margin-top: 16px">
      <table class="data-table">
        <thead><tr><th>No.</th><th>Summary</th><th>Topic</th><th>Avg.</th><th>Words</th><th class="center">Action</th></tr></thead>
        <tbody>
          <tr v-for="row in questions" :key="row.question_no">
            <td>{{ row.question_no }}</td><td>{{ row.summary }}</td><td>{{ row.topic }}</td><td>{{ row.avg_score }}</td><td>{{ row.word_count }}</td>
            <td class="center"><router-link :to="`/${row.question_no}/prepare`" class="btn small primary">Start Practice</router-link></td>
          </tr>
        </tbody>
      </table>
    </div>
  </AppShell>
</template>

