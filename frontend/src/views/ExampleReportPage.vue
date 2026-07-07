<script setup lang="ts">
import AppShell from '../components/AppShell.vue'

const exampleReportUrl = '/static/table/Record/Discussion%20Page%208,%201780879540.1451404.html'
</script>

<template>
  <AppShell>
    <section class="example-report-frame panel">
      <iframe :src="exampleReportUrl" title="Discussion Page 8 Example Report"></iframe>
    </section>
  </AppShell>
</template>
