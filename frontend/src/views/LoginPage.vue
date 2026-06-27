<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import PublicHeader from '../components/PublicHeader.vue'
import { apiPost } from '../api/client'

const router = useRouter()
const form = reactive({ identifier: '', password: '', captcha_token: '' })
async function login() { await apiPost('/auth/login', form); await router.push('/dashboard') }
</script>

<template>
  <div class="page-shell">
    <PublicHeader />
    <main class="container main-space form-grid auth-layout">
      <div>
        <h1 class="simple-title auth-title">Login to TAWEP</h1>
        <p class="muted">Use your user ID or email address. Password reset can be sent to your registered email.</p>
      </div>
      <form class="panel panel-pad" @submit.prevent="login">
        <label class="form-field">User ID or email<input v-model="form.identifier" class="input" /></label>
        <label class="form-field">Password<input v-model="form.password" type="password" class="input" /></label>
        <label class="form-field">Captcha<input v-model="form.captcha_token" class="input" placeholder="Enter captcha result" /></label>
        <button class="btn primary" type="submit">Login</button>
        <button class="btn ghost" type="button" style="margin-left:10px">Send password reset email</button>
      </form>
    </main>
  </div>
</template>
