<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useMessage } from 'naive-ui'
import AppShell from '../components/AppShell.vue'
import { apiGet, apiPost } from '../api/client'

const message = useMessage()
const topics = ref<string[]>([])
const form = reactive({ topic: '', difficulty: 'medium', student_a_name: '', student_a_content: '', student_b_name: '', student_b_content: '', professor_name: '', professor_content: '' })

async function submit() {
  await apiPost('/questions/upload', form)
  message.success('Question submitted for review')
}

onMounted(async () => { topics.value = await apiGet('/questions/topics'); form.topic = topics.value[0] || '' })
</script>

<template>
  <AppShell>
    <h1 class="simple-title">Create your own discussion prompt</h1>
    <form class="panel panel-pad" @submit.prevent="submit">
      <div class="form-grid">
        <label class="form-field">Topic<select v-model="form.topic" class="select"><option v-for="topic in topics" :key="topic" :value="topic">{{ topic }}</option></select></label>
        <label class="form-field">Difficulty<select v-model="form.difficulty" class="select"><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
      </div>
      <label class="form-field">Professor Name<input v-model="form.professor_name" class="input" /></label>
      <label class="form-field">Professor Content<textarea v-model="form.professor_content" class="textarea"></textarea></label>
      <div class="form-grid">
        <label class="form-field">Student A Name<input v-model="form.student_a_name" class="input" /></label>
        <label class="form-field">Student B Name<input v-model="form.student_b_name" class="input" /></label>
      </div>
      <div class="form-grid">
        <label class="form-field">Student A Content<textarea v-model="form.student_a_content" class="textarea"></textarea></label>
        <label class="form-field">Student B Content<textarea v-model="form.student_b_content" class="textarea"></textarea></label>
      </div>
      <button class="btn primary" type="submit">Submit</button>
    </form>
  </AppShell>
</template>
