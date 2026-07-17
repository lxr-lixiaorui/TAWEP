<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { darkTheme, type GlobalThemeOverrides } from 'naive-ui'
import { useAppStore } from './stores/app'

const app = useAppStore()
const theme = computed(() => (app.theme === 'dark' ? darkTheme : null))
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#006d6f',
    primaryColorHover: '#00888b',
    primaryColorPressed: '#00585a',
    borderRadius: '4px',
    fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
  }
}

onMounted(() => {
  app.applyTheme()
})
</script>

<template>
  <n-config-provider :theme="theme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <router-view />
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>
