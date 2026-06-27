<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useMessage } from 'naive-ui'
import AdminShell from '../../components/AdminShell.vue'
import { apiGet, apiPost } from '../../api/client'
const message = useMessage()
const rows = ref<any[]>([])
async function decide(id: string, action: 'accept' | 'reject') { await apiPost(`/admin/review-questions/${id}/${action}`, { comment: '' }); message.success(`Question ${action}ed`) }
onMounted(async () => { rows.value = await apiGet('/admin/review-questions') })
</script>

<template>
  <AdminShell>
    <h1 class="simple-title">User Upload Review</h1>
    <div class="panel"><table class="data-table"><thead><tr><th>ID</th><th>Topic</th><th>Status</th><th>Decision</th></tr></thead><tbody><tr v-for="row in rows" :key="row.id"><td>{{ row.id }}</td><td>{{ row.topic }}</td><td>{{ row.status }}</td><td><button class="btn small primary" @click="decide(row.id, 'accept')">Accept</button> <button class="btn small" @click="decide(row.id, 'reject')">Reject</button></td></tr></tbody></table></div>
  </AdminShell>
</template>
