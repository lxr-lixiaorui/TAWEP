<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowRight,
  BookOpenText,
  ChartNoAxesCombined,
  Check,
  FileSearch,
  Pause,
  Play,
  ScanText,
  WandSparkles
} from '@lucide/vue'
import PublicHeader from '../components/PublicHeader.vue'
import SiteFooter from '../components/SiteFooter.vue'
import { apiGet } from '../api/client'

interface QuestionBankStats {
  question_count: number
  topic_count: number
}

const { locale, t } = useI18n()
const demoVideo = ref<HTMLVideoElement | null>(null)
const demoPlaying = ref(false)
const demoLanguage = computed(() => locale.value.startsWith('zh') ? 'zh' : 'en')
const demoAssetVersion = 'native-ui-v3'
const demoSources = computed(() => ({
  webm: `/media/tawep-report-demo-${demoLanguage.value}.webm?v=${demoAssetVersion}`,
  mp4: `/media/tawep-report-demo-${demoLanguage.value}.mp4?v=${demoAssetVersion}`,
  poster: `/media/tawep-report-demo-${demoLanguage.value}-poster.jpg?v=${demoAssetVersion}`
}))
const prefersReducedMotion = ref(typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches)
const questionCount = ref<number | null>(null)
const topicCount = ref<number | null>(null)
const displayedQuestionCount = ref(0)
const displayedTopicCount = ref(0)
const displayedDimensions = ref(0)
let motionPreference: MediaQueryList | null = null
const countAnimations = new Set<number>()

function animateCount(target: number, value: { value: number }) {
  value.value = 0
  if (prefersReducedMotion.value || target <= 0) {
    value.value = target
    return
  }
  const startedAt = performance.now()
  let frameId = 0
  const update = (now: number) => {
    countAnimations.delete(frameId)
    const progress = Math.min((now - startedAt) / 1300, 1)
    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
    value.value = Math.min(target, Math.round(target * eased))
    if (progress < 1) {
      frameId = window.requestAnimationFrame(update)
      countAnimations.add(frameId)
    }
  }
  frameId = window.requestAnimationFrame(update)
  countAnimations.add(frameId)
}

async function loadQuestionStats() {
  try {
    const result = await apiGet<QuestionBankStats>('/questions/stats')
    questionCount.value = result.question_count
    topicCount.value = result.topic_count
    animateCount(result.question_count, displayedQuestionCount)
    animateCount(result.topic_count, displayedTopicCount)
    animateCount(4, displayedDimensions)
  } catch {
    displayedDimensions.value = 4
  }
}

const demoCopy = computed(() => locale.value.startsWith('zh')
  ? {
      label: 'TAWEP 答题与报告功能演示',
      play: '播放功能演示',
      pause: '暂停功能演示'
    }
  : {
      label: 'TAWEP answer and report feature demonstration',
      play: 'Play feature demonstration',
      pause: 'Pause feature demonstration'
    })

async function playDemo() {
  if (!demoVideo.value) return
  try {
    await demoVideo.value.play()
    demoPlaying.value = true
  } catch {
    demoPlaying.value = false
  }
}

watch(demoLanguage, async () => {
  demoPlaying.value = false
  await nextTick()
  demoVideo.value?.load()
  if (!prefersReducedMotion.value) void playDemo()
})

function toggleDemoPlayback() {
  if (!demoVideo.value) return
  if (demoPlaying.value) {
    demoVideo.value.pause()
    demoPlaying.value = false
    return
  }
  void playDemo()
}

function applyMotionPreference(event?: MediaQueryListEvent) {
  prefersReducedMotion.value = event?.matches ?? motionPreference?.matches ?? false
  if (prefersReducedMotion.value) {
    demoVideo.value?.pause()
    demoPlaying.value = false
    countAnimations.forEach((frame) => window.cancelAnimationFrame(frame))
    countAnimations.clear()
    if (questionCount.value !== null) displayedQuestionCount.value = questionCount.value
    if (topicCount.value !== null) displayedTopicCount.value = topicCount.value
    displayedDimensions.value = 4
  } else {
    void playDemo()
  }
}

onMounted(() => {
  motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)')
  motionPreference.addEventListener('change', applyMotionPreference)
  applyMotionPreference()
  void loadQuestionStats()
})

onUnmounted(() => {
  motionPreference?.removeEventListener('change', applyMotionPreference)
  countAnimations.forEach((frame) => window.cancelAnimationFrame(frame))
  countAnimations.clear()
})

const stats = computed(() => [
  [questionCount.value === null ? '—' : String(displayedQuestionCount.value), t('home.stats.prompts')],
  [topicCount.value === null ? '—' : String(displayedTopicCount.value), t('home.stats.topics')],
  ['0', t('home.stats.cost')],
  [String(displayedDimensions.value), t('home.stats.dimensions')]
])

const workflow = computed(() => [
  { number: '01', title: t('home.workflow.chooseTitle'), body: t('home.workflow.chooseBody') },
  { number: '02', title: t('home.workflow.writeTitle'), body: t('home.workflow.writeBody') },
  { number: '03', title: t('home.workflow.improveTitle'), body: t('home.workflow.improveBody') }
])

const reportLayers = computed(() => [
  { icon: ChartNoAxesCombined, title: t('home.layers.scoreTitle'), body: t('home.layers.scoreBody') },
  { icon: FileSearch, title: t('home.layers.diagnosisTitle'), body: t('home.layers.diagnosisBody') },
  { icon: ScanText, title: t('home.layers.grammarTitle'), body: t('home.layers.grammarBody') },
  { icon: WandSparkles, title: t('home.layers.rewriteTitle'), body: t('home.layers.rewriteBody') }
])

const topics = [
  'Education', 'Environment', 'Policy', 'Business', 'Technology',
  'Consumer Behavior', 'Health', 'Culture', 'Lifelong Learning'
]
</script>

<template>
  <div class="page-shell home-page">
    <PublicHeader />
    <main>
      <section class="home-hero">
        <div class="container home-hero-layout intro-fade intro-fade-1">
          <div class="home-hero-copy">
            <p class="home-offer"><Check :size="16" />{{ t('home.offer', { count: questionCount === null ? '—' : displayedQuestionCount }) }}</p>
            <h1>{{ t('home.title') }}</h1>
            <p class="home-lead">{{ t('home.lead') }}</p>
            <div class="hero-actions">
              <router-link to="/questionbank" class="btn primary home-primary-cta">
                {{ t('home.start') }}<ArrowRight :size="18" />
              </router-link>
              <router-link to="/examplereport" class="btn home-report-link">{{ t('home.example') }}</router-link>
            </div>
            <p class="home-no-card">{{ t('home.noCard') }}</p>
          </div>

          <figure class="home-demo">
            <video
              :key="demoSources.mp4"
              ref="demoVideo"
              class="home-demo-video"
              :aria-label="demoCopy.label"
              :autoplay="!prefersReducedMotion"
              muted
              loop
              playsinline
              preload="auto"
              :poster="demoSources.poster"
              @play="demoPlaying = true"
              @pause="demoPlaying = false"
              @loadeddata="!prefersReducedMotion && playDemo()"
            >
              <source :src="demoSources.webm" type="video/webm" />
              <source :src="demoSources.mp4" type="video/mp4" />
            </video>
            <button
              type="button"
              class="home-demo-control"
              :aria-label="demoPlaying ? demoCopy.pause : demoCopy.play"
              :title="demoPlaying ? demoCopy.pause : demoCopy.play"
              @click="toggleDemoPlayback"
            >
              <Pause v-if="demoPlaying" :size="17" />
              <Play v-else :size="17" />
            </button>
          </figure>
        </div>
      </section>

      <section class="home-proof-rail" aria-label="TAWEP facts">
        <div class="container">
          <article v-for="item in stats" :key="item[1]">
            <strong>{{ item[0] }}</strong>
            <span>{{ item[1] }}</span>
          </article>
        </div>
      </section>

      <section class="home-section container home-workflow intro-fade intro-fade-2">
        <div class="home-section-intro">
          <p class="eyebrow">{{ t('home.workflow.overline') }}</p>
          <h2>{{ t('home.workflow.title') }}</h2>
          <p>{{ t('home.workflow.body') }}</p>
        </div>
        <div class="workflow-list">
          <article v-for="step in workflow" :key="step.number">
            <span>{{ step.number }}</span>
            <div><h3>{{ step.title }}</h3><p>{{ step.body }}</p></div>
          </article>
        </div>
      </section>

      <section class="home-report-band">
        <div class="container home-report-layout intro-fade intro-fade-3">
          <div class="report-layer-list">
            <article v-for="layer in reportLayers" :key="layer.title">
              <component :is="layer.icon" :size="20" />
              <div><h3>{{ layer.title }}</h3><p>{{ layer.body }}</p></div>
            </article>
          </div>
          <div class="report-band-focus">
            <p class="eyebrow">{{ t('home.report.overline') }}</p>
            <h2>{{ t('home.report.title') }}</h2>
            <p>{{ t('home.report.body') }}</p>
            <router-link class="text-link light" to="/examplereport">
              {{ t('home.report.open') }}<ArrowRight :size="17" />
            </router-link>
          </div>
        </div>
      </section>

      <section class="home-section container home-topics intro-fade intro-fade-4">
        <div class="home-section-intro">
          <p class="eyebrow">{{ t('home.bank.overline') }}</p>
          <h2>{{ t('home.bank.title') }}</h2>
          <p>{{ t('home.bank.body', {
            count: questionCount === null ? '—' : displayedQuestionCount,
            topics: topicCount === null ? '—' : displayedTopicCount
          }) }}</p>
          <router-link class="text-link" to="/questionbank">
            {{ t('home.bank.browse') }}<ArrowRight :size="17" />
          </router-link>
        </div>
        <div class="topic-index">
          <span v-for="(topic, index) in topics" :key="topic">
            <small>{{ String(index + 1).padStart(2, '0') }}</small>{{ topic }}
          </span>
        </div>
      </section>

      <section class="home-final-band">
        <div class="container">
          <BookOpenText :size="28" />
          <div><h2>{{ t('home.final.title') }}</h2><p>{{ t('home.final.body') }}</p></div>
          <router-link class="btn attention-cta" to="/questionbank">
            {{ t('home.final.action') }}<ArrowRight :size="18" />
          </router-link>
        </div>
      </section>
    </main>
    <SiteFooter />
  </div>
</template>
