<script setup lang="ts">
import { ExternalLink, MessageCircle } from '@lucide/vue'
import { computed } from 'vue'
import { useAppStore } from '../stores/app'

const app = useAppStore()
const discordUrl = String(import.meta.env.VITE_DISCORD_INVITE_URL || '').trim()
const copy = computed(() => app.locale === 'zh'
  ? {
      title: '加入我们的 Discord 社区',
      body: '讨论学术写作、分享练习体验，并关注 TAWEP 的后续更新。',
      action: '加入 Discord',
      pending: 'Discord 邀请链接即将开放',
      agreements: '协议中心'
    }
  : {
      title: 'Join our Discord server',
      body: 'Discuss academic writing, share practice feedback, and follow TAWEP updates.',
      action: 'Join Discord',
      pending: 'Discord invite coming soon',
      agreements: 'Agreements'
    })
</script>

<template>
  <footer class="site-footer">
    <div class="site-footer-unified">
      <div class="container site-footer-inner">
        <div class="discord-footer-copy">
          <MessageCircle :size="24" />
          <div><strong>{{ copy.title }}</strong><span>{{ copy.body }}</span></div>
        </div>
        <div class="site-footer-side">
          <a v-if="discordUrl" class="btn discord-footer-button" :href="discordUrl" target="_blank" rel="noopener noreferrer">
            {{ copy.action }}<ExternalLink :size="16" />
          </a>
          <button v-else class="btn discord-footer-button" type="button" disabled :title="copy.pending">
            {{ copy.action }}<ExternalLink :size="16" />
          </button>
          <div class="site-footer-meta">
            <span>TAWEP · TOEFL Academic Discussion Evaluation Project</span>
            <span>Developed by WFLA AI Lab</span>
            <nav>
              <router-link to="/agreements">{{ copy.agreements }}</router-link>
              <a href="mailto:feedback@tawep.org">feedback@tawep.org</a>
              <a href="https://github.com/lxr-lixiaorui/TAWEP/" target="_blank" rel="noopener noreferrer">GitHub<ExternalLink :size="13" /></a>
            </nav>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>
