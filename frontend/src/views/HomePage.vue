<script setup lang="ts">
import PublicHeader from '../components/PublicHeader.vue'

const stats = [
  ['96', 'official Academic Discussion prompts'],
  ['9', 'automatically classified topic groups'],
  ['0', 'cost to start practicing'],
  ['4', 'scored writing dimensions']
]

const reportMatrix = [
  ['Score', '30-point total, 5-point rubric score, and four dimension scores.'],
  ['Diagnosis', 'Content, expansion, language, logic, grammar, spelling, and wording issues.'],
  ['Action Plan', 'Specific edits and priority guidance instead of generic comments.'],
  ['Rewrite', 'A polished response that preserves the student position and improves execution.'],
  ['Style Profile', 'Writing habits and academic style patterns; later releases will use this to personalize rewrites.'],
  ['Progress View', 'Topic and dimension history for finding repeated weaknesses.']
]

const topics = [
  'Education',
  'Environment',
  'Policy',
  'Business',
  'Technology',
  'Consumer Behavior',
  'Health',
  'Culture',
  'Lifelong Learning'
]
</script>

<template>
  <div class="page-shell">
    <PublicHeader />
    <main>
      <section class="hero-layout">
        <div class="hero-copy container">
          <div>
            <p class="eyebrow">Free TOEFL Academic Discussion practice</p>
            <h1>Practice every prompt, then get feedback you can actually use.</h1>
            <p>
              TAWEP is built for repeat practice: a full question bank, automatic topic
              classification, calibrated AI scoring, and reports that explain what to fix in the
              next draft rather than only judging the last one.
            </p>
            <div class="hero-actions">
              <router-link to="/questionbank" class="btn primary">Start Free Practice</router-link>
              <router-link to="/examplereport" class="btn">See Example Report</router-link>
            </div>
          </div>
        </div>

        <section class="intro-proof container">
          <div v-for="item in stats" :key="item[1]" class="proof-stat">
            <strong>{{ item[0] }}</strong>
            <span>{{ item[1] }}</span>
          </div>
        </section>

        <section class="intro-section container intro-split">
          <div>
            <p class="eyebrow">Question bank</p>
            <h2 class="section-title">Every current prompt is free and sorted by topic.</h2>
            <p class="section-copy">
              The current legacy bank parses into 96 Academic Discussion questions. TAWEP groups
              them into topic buckets automatically, so students can drill a weak area instead of
              scrolling through a flat list.
            </p>
          </div>
          <div class="topic-grid">
            <span v-for="topic in topics" :key="topic">{{ topic }}</span>
          </div>
        </section>

        <section class="intro-section container">
          <div class="section-head">
            <div>
              <p class="eyebrow">Report matrix</p>
              <h2 class="section-title">One report, multiple layers of feedback.</h2>
            </div>
            <p class="section-copy compact">
              The scoring model gives the first pass today. The roadmap is a larger language model
              plus math-model calibration so scores and advice become more stable over time.
            </p>
          </div>
          <div class="report-matrix">
            <article v-for="item in reportMatrix" :key="item[0]" class="report-cell">
              <strong>{{ item[0] }}</strong>
              <p>{{ item[1] }}</p>
            </article>
          </div>
        </section>

        <section class="intro-section container intro-split">
          <div>
            <p class="eyebrow">Actionable improvement</p>
            <h2 class="section-title">Advice should change the next essay, not just label this one.</h2>
          </div>
          <div class="roadmap-panel">
            <p>
              TAWEP can already produce focused recommendations and an AI Rewrite. The next model
              direction is personal style analysis: learn a student's academic writing patterns,
              then make rewrites that sound like a stronger version of that same writer.
            </p>
            <router-link to="/questionbank" class="btn primary">Choose a Prompt</router-link>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>
