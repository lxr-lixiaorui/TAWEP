<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPost } from '../api/client'

const route = useRoute()
const router = useRouter()
const questionNo = Number(route.params.questionNo)
const question = ref<any | null>(null)

async function start(mode: 'timed' | 'unlimited') {
  const session = await apiPost<any>(`/questions/${questionNo}/sessions`, { mode })
  await router.push(`/${session.id}/answerpage`)
}

onMounted(async () => { question.value = await apiGet(`/questions/${questionNo}`) })
</script>

<template>
  <AppShell>
    <div v-if="question">
      <p class="muted">Question {{ question.question_no }}</p>
      <h1 class="simple-title">{{ question.question_no }}. {{ question.summary }}</h1>
      <div class="form-grid" style="margin: 24px 0">
        <article v-for="msg in question.messages" :key="msg.sort_order" class="panel panel-pad">
          <strong>{{ msg.speaker_name }}</strong><p class="muted">{{ msg.content }}</p>
        </article>
      </div>
      <div class="hero-actions">
        <button class="btn primary" @click="start('timed')">Timed 10-minute Simulation</button>
        <button class="btn" @click="start('unlimited')">Untimed Practice</button>
      </div>
    </div>
  </AppShell>
</template>
