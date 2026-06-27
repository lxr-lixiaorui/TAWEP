<template>
  <div class="page-shell">
    <div class="admin-layout">
      <aside class="panel admin-side">
        <router-link class="brand-title" to="/manage/questionbank">TAWEP</router-link>
        <router-link to="/manage/questionbank">Question Bank</router-link>
        <router-link to="/manage/reviewquestion">Review Uploads</router-link>
        <router-link to="/manage/accounts">Accounts</router-link>
      </aside>
      <main class="admin-main">
        <slot />
      </main>
    </div>
  </div>
</template>
