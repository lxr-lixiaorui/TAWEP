<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowRight,
  BookOpenText,
  ChartNoAxesCombined,
  Check,
  FileSearch,
  ScanText,
  WandSparkles
} from '@lucide/vue'
import PublicHeader from '../components/PublicHeader.vue'

const { t } = useI18n()

const stats = computed(() => [
  ['96', t('home.stats.prompts')],
  ['9', t('home.stats.topics')],
  ['0', t('home.stats.cost')],
  ['4', t('home.stats.dimensions')]
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
        <img src="/images/tawep-report-preview.png" alt="TAWEP evaluation report with score breakdown and prioritized feedback" />
        <div class="home-hero-shade" aria-hidden="true"></div>
        <div class="container home-hero-content intro-fade intro-fade-1">
          <p class="home-offer"><Check :size="16" />{{ t('home.offer') }}</p>
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
          <div class="report-band-focus">
            <p class="eyebrow">{{ t('home.report.overline') }}</p>
            <h2>{{ t('home.report.title') }}</h2>
            <p>{{ t('home.report.body') }}</p>
            <router-link class="text-link light" to="/examplereport">
              {{ t('home.report.open') }}<ArrowRight :size="17" />
            </router-link>
          </div>
          <div class="report-layer-list">
            <article v-for="layer in reportLayers" :key="layer.title">
              <component :is="layer.icon" :size="20" />
              <div><h3>{{ layer.title }}</h3><p>{{ layer.body }}</p></div>
            </article>
          </div>
        </div>
      </section>

      <section class="home-section container home-topics intro-fade intro-fade-4">
        <div class="home-section-intro">
          <p class="eyebrow">{{ t('home.bank.overline') }}</p>
          <h2>{{ t('home.bank.title') }}</h2>
          <p>{{ t('home.bank.body') }}</p>
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
  </div>
</template>
