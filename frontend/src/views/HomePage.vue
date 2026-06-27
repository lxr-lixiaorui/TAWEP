<script setup lang="ts">
import PublicHeader from '../components/PublicHeader.vue'

const rows = [
  ['Score Breakdown', true, true, true, false, false],
  ['Problem Analysis', true, true, true, false, false],
  ['Improvement Plan', true, true, true, true, false],
  ['AI Rewrite', true, false, true, true, false],
  ['Grammar Analysis', true, true, true, false, false],
  ['Language Preference', false, true, true, true, false],
  ['Topic Score Matrix', false, true, false, true, true]
]
</script>

<template>
  <div class="page-shell">
    <PublicHeader />
    <main>
      <section class="hero-layout">
        <div class="hero-copy container">
          <div>
            <h1>Free TOEFL Academic Discussion practice with calibrated AI feedback</h1>
            <p>
              TAWEP provides a free, topic-classified TOEFL Academic Discussion question bank,
              AI evaluation aligned with academic writing rubrics, and detailed reports that turn
              every submission into specific next steps.
            </p>
            <div class="hero-actions">
              <router-link to="/questionbank" class="btn primary">Start Free Practice</router-link>
              <router-link to="/examplereport" class="btn">See Example Report</router-link>
            </div>
          </div>
        </div>

        <section class="matrix-section container">
          <h2 class="section-title">Report capability matrix</h2>
          <table class="data-table">
            <thead>
              <tr>
                <th>Report Area</th>
                <th class="center">AI Scoring</th>
                <th class="center">Dimension<br />Breakdown</th>
                <th class="center">Actionable<br />Advice</th>
                <th class="center">Style<br />Modeling</th>
                <th class="center">Topic<br />Analytics</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="String(row[0])">
                <td>{{ row[0] }}</td>
                <td v-for="index in 5" :key="index" class="center">
                  <span :class="row[index] ? 'link-action' : 'muted'">{{ row[index] ? 'Yes' : '-' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="feature-row">
            <div class="feature-stat"><strong>Free to use</strong><span>Initial credits included</span></div>
            <div class="feature-stat"><strong>Full topic bank</strong><span>100+ classified prompts</span></div>
            <div class="feature-stat"><strong>Model-calibrated</strong><span>AI scoring now, math tuning later</span></div>
            <div class="feature-stat"><strong>Actionable reports</strong><span>Rewrite, grammar, matrix, next steps</span></div>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>
