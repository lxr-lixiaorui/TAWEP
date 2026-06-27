<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useMessage } from 'naive-ui'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPatch } from '../api/client'

const message = useMessage()
const user = reactive({ alias: '', preferred_locale: 'en', theme: 'light' })
const usage = ref<any | null>(null)

async function save() { await apiPatch('/me', user); message.success('Settings saved') }
onMounted(async () => { const me = await apiGet<any>('/me'); Object.assign(user, me); usage.value = await apiGet('/me/usage') })
</script>

<template>
  <AppShell>
    <h1 class="simple-title">Settings</h1>
    <section class="form-grid">
      <form class="panel panel-pad" @submit.prevent="save">
        <h2>Personal Info</h2>
        <label class="form-field">Alias<input v-model="user.alias" class="input" /></label>
        <label class="form-field">Website Language<select v-model="user.preferred_locale" class="select"><option value="en">English</option><option value="zh">中文</option></select></label>
        <label class="form-field">Theme<select v-model="user.theme" class="select"><option value="light">Light</option><option value="dark">Dark</option><option value="system">System</option></select></label>
        <button class="btn primary" type="submit">Save</button>
      </form>
      <div class="panel panel-pad"><h2>Usage</h2><p><strong>{{ usage?.balance ?? 180 }}</strong> current credits</p><p class="muted">{{ usage?.weekly_used ?? 0 }} / {{ usage?.weekly_limit ?? 60 }} weekly credits used</p><p class="muted">{{ usage?.total_planned_credit ?? 180 }} total planned credit</p></div>
    </section>
    <section class="panel panel-pad" style="margin-top: 18px"><h2>Others</h2><div class="hero-actions"><router-link to="/agreements" class="btn">Agreements</router-link><router-link to="/creditexplanation" class="btn">Credit explanation</router-link><a href="https://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank" class="btn">GPL-3 open source rule</a></div></section>
  </AppShell>
</template>
