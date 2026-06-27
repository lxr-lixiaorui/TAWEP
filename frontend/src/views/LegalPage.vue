<script setup lang="ts">
import { computed } from 'vue'
import AppShell from '../components/AppShell.vue'
const props = defineProps<{ slug: string }>()
const title = computed(() => (props.slug === 'agreements' ? 'Agreements' : 'Credit Explanation'))
</script>

<template>
  <AppShell>
    <article class="panel panel-pad" style="max-width: 820px">
      <h1 class="simple-title">{{ title }}</h1>
      <p v-if="slug === 'agreements'" class="muted">
        TAWEP stores practice data, reports, and credit usage to provide writing evaluation and progress tracking.
        The platform should not store API keys, raw passwords, or private TOEFL materials uploaded without permission.
      </p>
      <p v-else class="muted">
        Each full AI evaluation consumes 3 credits. New accounts receive 180 credits, and each account can consume up to
        60 credits in a rolling 7-day window. Accepted user-uploaded questions can receive additional planned credits.
      </p>
    </article>
  </AppShell>
</template>
