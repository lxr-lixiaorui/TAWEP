<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const exampleSessionId = '00000000-0000-4000-8000-000000000008'

onMounted(() => {
  void router.replace(`/${exampleSessionId}/report`)
})
</script>

<template>
  <main class="redirect-page">
    <p>Opening example report...</p>
  </main>
</template>
