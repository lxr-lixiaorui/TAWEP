import { LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, RadarComponent, TooltipComponent } from 'echarts/components'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import naive from 'naive-ui'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import VueECharts from 'vue-echarts'

import App from './App.vue'
import { i18n } from './i18n'
import { router } from './router'
import './styles/theme.css'

use([
  CanvasRenderer,
  LineChart,
  RadarChart,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent
])

createApp(App)
  .use(createPinia())
  .use(router)
  .use(i18n)
  .use(naive)
  .component('VChart', VueECharts)
  .mount('#app')
