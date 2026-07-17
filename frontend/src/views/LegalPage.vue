<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowLeft, FileText } from '@lucide/vue'
import PublicHeader from '../components/PublicHeader.vue'
import { apiGet } from '../api/client'
import { useAppStore } from '../stores/app'

type DocumentSummary = { slug: string; title: string; summary: string; version: string }
type LegalSection = { heading: string; paragraphs: string[]; bullets: string[] }
type LegalDocument = DocumentSummary & { updated_at: string; sections: LegalSection[] }

const props = defineProps<{ slug?: string }>()
const app = useAppStore()
const loading = ref(false)
const error = ref('')
const documents = ref<DocumentSummary[]>([])
const document = ref<LegalDocument | null>(null)
const copy = computed(() => app.locale === 'zh' ? {
  eyebrow: '法律与服务文件', title: '协议中心', subtitle: '在一个位置查看当前有效的协议、隐私规则和专项声明。',
  back: '返回协议中心', version: '版本', updated: '更新日期', loadError: '暂时无法加载该文件。'
} : {
  eyebrow: 'Legal and service documents', title: 'Agreement center', subtitle: 'Review the current agreements, privacy rules, and specific notices in one place.',
  back: 'Back to agreement center', version: 'Version', updated: 'Updated', loadError: 'This document could not be loaded.'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (props.slug) {
      document.value = await apiGet<LegalDocument>(`/legal/documents/${props.slug}?locale=${app.locale}`)
      documents.value = []
    } else {
      documents.value = await apiGet<DocumentSummary[]>(`/legal/documents?locale=${app.locale}`)
      document.value = null
    }
  } catch (value) {
    error.value = value instanceof Error ? value.message : copy.value.loadError
  } finally {
    loading.value = false
  }
}

watch(() => [props.slug, app.locale], load, { immediate: true })
</script>

<template>
  <div class="page-shell">
    <PublicHeader />
    <main class="container main-space legal-page">
      <router-link v-if="slug" class="legal-back" to="/agreements"><ArrowLeft :size="16" />{{ copy.back }}</router-link>
      <header class="legal-head">
        <p class="eyebrow">{{ copy.eyebrow }}</p>
        <h1 class="simple-title">{{ document?.title || copy.title }}</h1>
        <p>{{ document?.summary || copy.subtitle }}</p>
        <div v-if="document" class="legal-meta">
          <span>{{ copy.version }} {{ document.version }}</span>
          <span>{{ copy.updated }} {{ document.updated_at }}</span>
        </div>
      </header>

      <div v-if="loading" class="panel panel-pad legal-state"><n-skeleton text :repeat="7" /></div>
      <div v-else-if="error" class="panel panel-pad legal-state error" role="alert">{{ error }}</div>

      <section v-else-if="!slug" class="legal-index">
        <router-link v-for="item in documents" :key="item.slug" class="legal-document-card panel" :to="`/agreements/${item.slug}`">
          <FileText :size="22" />
          <div><h2>{{ item.title }}</h2><p>{{ item.summary }}</p><small>{{ copy.version }} {{ item.version }}</small></div>
        </router-link>
      </section>

      <article v-else-if="document" class="legal-document panel">
        <section v-for="section in document.sections" :key="section.heading" class="legal-section">
          <h2>{{ section.heading }}</h2>
          <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
          <ul v-if="section.bullets.length"><li v-for="item in section.bullets" :key="item">{{ item }}</li></ul>
        </section>
      </article>
    </main>
  </div>
</template>
