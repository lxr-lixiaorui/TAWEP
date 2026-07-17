<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Eye, EyeOff, ShieldCheck, X } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import AdminShell from '../../components/AdminShell.vue'
import { apiGet, apiPatch } from '../../api/client'

type CrossBorderConfig = {
  visible: boolean
  consent_version: string | null
  activation: number
  updated_at: string | null
}

const message = useMessage()
const config = ref<CrossBorderConfig | null>(null)
const loading = ref(true)
const saving = ref(false)
const activationOpen = ref(false)

async function loadConfig() {
  loading.value = true
  try {
    config.value = await apiGet<CrossBorderConfig>('/admin/legal/cross-border')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to load platform settings')
  } finally {
    loading.value = false
  }
}

async function updateVisibility(visible: boolean) {
  saving.value = true
  try {
    config.value = await apiPatch<CrossBorderConfig>('/admin/legal/cross-border', { visible })
    activationOpen.value = false
    message.success(visible ? 'The notice is visible and renewed consent is now required.' : 'The notice is hidden.')
  } catch (error) {
    message.error(error instanceof Error ? error.message : 'Unable to update the setting')
  } finally {
    saving.value = false
  }
}

function requestVisibility(value: boolean) {
  if (value && !config.value?.visible) activationOpen.value = true
  else void updateVisibility(value)
}

onMounted(loadConfig)
</script>

<template>
  <AdminShell>
    <header class="admin-page-head">
      <div><p class="eyebrow">Administration</p><h1>Platform Settings</h1><p>Control user-facing legal requirements and platform behavior.</p></div>
    </header>

    <section class="panel admin-setting-card">
      <div class="admin-setting-icon" :class="config?.visible ? 'active' : ''">
        <Eye v-if="config?.visible" :size="23" /><EyeOff v-else :size="23" />
      </div>
      <div class="admin-setting-copy">
        <p class="eyebrow">Legal visibility</p>
        <h2>Cross-border Processing Notice</h2>
        <p>When hidden, the notice is removed from Agreements and registration. Turning it on creates a new activation version and asks every user to consent on their next visit.</p>
        <dl v-if="config" class="admin-setting-meta">
          <div><dt>Status</dt><dd>{{ config.visible ? 'Visible' : 'Invisible' }}</dd></div>
          <div><dt>Activation</dt><dd>#{{ config.activation }}</dd></div>
          <div><dt>Consent version</dt><dd>{{ config.consent_version || 'Not activated' }}</dd></div>
        </dl>
      </div>
      <div class="admin-setting-control">
        <span>{{ config?.visible ? 'Visible' : 'Invisible' }}</span>
        <n-switch :value="Boolean(config?.visible)" :loading="loading || saving" @update:value="requestVisibility" />
      </div>
    </section>

    <n-modal v-model:show="activationOpen">
      <section class="panel admin-dialog legal-activation-dialog" role="dialog" aria-modal="true" aria-labelledby="legal-activation-title">
        <header><div><p class="eyebrow">Renewed consent</p><h2 id="legal-activation-title">Make this notice visible?</h2></div><button class="btn ghost small icon-btn" title="Close" aria-label="Close" @click="activationOpen = false"><X :size="17" /></button></header>
        <div class="legal-activation-warning"><ShieldCheck :size="24" /><p>Every registered user, including users who accepted an older version, will see a required consent dialog on their next visit.</p></div>
        <footer><button class="btn" type="button" @click="activationOpen = false">Cancel</button><button class="btn primary" type="button" :disabled="saving" @click="updateVisibility(true)">Activate and require consent</button></footer>
      </section>
    </n-modal>
  </AdminShell>
</template>
