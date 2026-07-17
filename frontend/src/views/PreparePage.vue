<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { CircleAlert, Settings2 } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import { ApiError, apiGet, apiPost } from '../api/client'
import { useAppStore } from '../stores/app'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const questionNo = Number(route.params.questionNo)
const question = ref<any | null>(null)
const usage = ref<any | null>(null)
const starting = ref(false)
const insufficient = ref(false)
const copy = computed(() => app.locale === 'zh' ? {
  question: '第 {number} 题', timed: '10 分钟限时模拟', untimed: '不限时练习',
  runOut: 'Credits 不足', runOutBody: '剩余额度不足以支付一次完整评分，因此不会创建正常评分练习。个人 API 仍消耗相同 credits。',
  setup: '设置自己的大语言模型 API', explanation: '查看 credits 说明'
} : {
  question: 'Question {number}', timed: 'Timed 10-minute simulation', untimed: 'Untimed practice',
  runOut: 'Run out of credits', runOutBody: 'The remaining balance cannot cover a full evaluation, so a normal scored session will not be created. A personal API still uses the same credits.',
  setup: 'Use your own Large-Language-Model API', explanation: 'Read the credit explanation'
})

function format(value: string, number: number) {
  return value.replace('{number}', String(number))
}

async function start(mode: 'timed' | 'unlimited') {
  if (insufficient.value || !usage.value?.can_start_evaluation) {
    insufficient.value = true
    return
  }
  starting.value = true
  try {
    const session = await apiPost<any>(`/questions/${questionNo}/sessions`, { mode })
    await router.push(`/${session.id}/answerpage`)
  } catch (error) {
    if (error instanceof ApiError && error.code === 'INSUFFICIENT_CREDIT') insufficient.value = true
    else throw error
  } finally {
    starting.value = false
  }
}

onMounted(async () => {
  const [questionResult, usageResult] = await Promise.all([
    apiGet(`/questions/${questionNo}`), apiGet<any>('/me/usage')
  ])
  question.value = questionResult
  usage.value = usageResult
  insufficient.value = !usageResult.can_start_evaluation
})
</script>

<template>
  <AppShell>
    <div v-if="question" class="prepare-layout">
      <div class="prepare-card panel panel-pad">
        <p class="eyebrow">{{ format(copy.question, question.question_no) }}</p>
        <h1 class="simple-title">{{ question.summary }}</h1>
        <aside v-if="insufficient" class="credit-blocker" role="alert">
          <CircleAlert :size="24" />
          <div><strong>{{ copy.runOut }}</strong><p>{{ copy.runOutBody }}</p>
            <div class="credit-blocker-links">
              <router-link class="btn primary" to="/settings?tab=usage"><Settings2 :size="16" />{{ copy.setup }}</router-link>
              <router-link to="/agreements/credit-explanation">{{ copy.explanation }}</router-link>
            </div>
          </div>
        </aside>
        <div v-else class="hero-actions">
          <button class="btn primary" :disabled="starting" @click="start('timed')">{{ copy.timed }}</button>
          <button class="btn" :disabled="starting" @click="start('unlimited')">{{ copy.untimed }}</button>
        </div>
      </div>
    </div>
  </AppShell>
</template>
