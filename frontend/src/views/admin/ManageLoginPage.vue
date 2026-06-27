<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="page-shell">
    <main class="container main-space form-grid auth-layout">
      <div>
        <h1 class="simple-title auth-title">TAWEP Manage</h1>
        <p class="muted">Administrator access for question review, question bank moderation, and account operations.</p>
      </div>
      <form class="panel panel-pad" @submit.prevent="router.push('/manage/questionbank')">
        <label class="form-field">Admin ID<input class="input" /></label>
        <label class="form-field">Password<input class="input" type="password" /></label>
        <button class="btn primary" type="submit">Login</button>
      </form>
    </main>
  </div>
</template>
