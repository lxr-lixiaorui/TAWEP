<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { apiGet } from '../api/client'

const messages = ref<any[]>([])
onMounted(async () => { messages.value = await apiGet('/me/inbox') })
</script>

<template>
  <AppShell>
    <h1 class="simple-title">Inbox</h1>
    <div style="display:grid; gap:14px">
      <article v-for="message in messages" :key="message.id" class="panel panel-pad">
        <div style="display:flex; justify-content:space-between; gap:20px"><strong>{{ message.title }}</strong><span class="muted">{{ new Date(message.created_at).toLocaleString() }}</span></div>
        <p>{{ message.body }}</p>
      </article>
    </div>
  </AppShell>
</template>
