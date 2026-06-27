<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AdminShell from '../../components/AdminShell.vue'
import { apiGet } from '../../api/client'
const rows = ref<any[]>([])
onMounted(async () => { rows.value = await apiGet('/admin/questions') })
</script>

<template>
  <AdminShell>
    <h1 class="simple-title">Question Bank Management</h1>
    <div class="panel"><table class="data-table"><thead><tr><th>No.</th><th>Source</th><th>Status</th><th>Action</th></tr></thead><tbody><tr v-for="row in rows" :key="row.question_no"><td>{{ row.question_no }}</td><td>{{ row.source }}</td><td>{{ row.status }}</td><td><button class="btn small">Edit</button></td></tr></tbody></table></div>
  </AdminShell>
</template>
