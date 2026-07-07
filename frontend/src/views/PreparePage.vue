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
    <div v-if="question" class="prepare-layout">
      <div class="prepare-card panel panel-pad">
        <p class="eyebrow">Question {{ question.question_no }}</p>
        <h1 class="simple-title">{{ question.summary }}</h1>
        <div class="hero-actions">
          <button class="btn primary" @click="start('timed')">Timed 10-minute Simulation</button>
          <button class="btn" @click="start('unlimited')">Untimed Practice</button>
        </div>
      </div>
    </div>
  </AppShell>
</template>
