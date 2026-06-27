import { createPinia } from 'pinia'
import { createApp } from 'vue'
import VueECharts from 'vue-echarts'
import naive from 'naive-ui'

import App from './App.vue'
import { i18n } from './i18n'
import { router } from './router'
import './styles/theme.css'

createApp(App)
  .use(createPinia())
  .use(router)
  .use(i18n)
  .use(naive)
  .component('VChart', VueECharts)
  .mount('#app')
