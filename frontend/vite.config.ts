import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:1145',
        changeOrigin: true
      },
      '/static': {
        target: 'http://127.0.0.1:1145',
        changeOrigin: true
      }
    }
  }
})
