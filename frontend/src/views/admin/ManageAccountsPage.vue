<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { apiGet, apiPatch, apiPost } from '../../api/client'
const rows = ref<any[]>([])
async function ban(id: string) { await apiPatch(`/admin/accounts/${id}/ban`, { comment: '' }) }
async function notify(id: string) { await apiPost(`/admin/accounts/${id}/messages`, { title: 'TAWEP notice', body: 'A system message from TAWEP.' }) }
onMounted(async () => { rows.value = await apiGet('/admin/accounts') })
</script>

<template>
  <AdminShell>
    <h1 class="simple-title">Accounts</h1>
    <div class="panel"><table class="data-table"><thead><tr><th>Email</th><th>Status</th><th>Credit</th><th>Action</th></tr></thead><tbody><tr v-for="row in rows" :key="row.id"><td>{{ row.email }}</td><td>{{ row.status }}</td><td>{{ row.credit }}</td><td><button class="btn small" @click="notify(row.id)">Notify</button> <button class="btn small" @click="ban(row.id)">Ban</button></td></tr></tbody></table></div>
  </AdminShell>
</template>
