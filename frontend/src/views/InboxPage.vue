<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowRight } from '@lucide/vue'
import AppShell from '../components/AppShell.vue'
import { apiGet } from '../api/client'
import { useAppStore } from '../stores/app'

const messages = ref<any[]>([])
const app = useAppStore()
const copy = computed(() => app.locale === 'zh' ? { title: '收件箱' } : { title: 'Inbox' })

onMounted(async () => {
  messages.value = await apiGet('/me/inbox')
})
</script>

<template>
  <AppShell>
    <h1 class="simple-title">{{ copy.title }}</h1>
    <div class="inbox-list">
      <article v-for="message in messages" :key="message.id" class="panel panel-pad inbox-message">
        <div class="inbox-message-head">
          <strong>{{ message.title }}</strong>
          <span class="muted">{{ new Date(message.created_at).toLocaleString() }}</span>
        </div>
        <p>{{ message.body }}</p>
        <router-link v-if="message.action_url" class="text-link inbox-action" :to="message.action_url">
          {{ message.action_label }}<ArrowRight :size="15" />
        </router-link>
      </article>
    </div>
  </AppShell>
</template>
