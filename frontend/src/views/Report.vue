<template>
  <div>
    <div style="margin-bottom:12px">
      <el-button type="primary" @click="load">刷新报告</el-button>
      <el-button @click="exportMd">导出 Markdown</el-button>
    </div>
    <el-card v-loading="loading">
      <div class="markdown-body" v-html="rendered" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { getReport } from '@/api'

const route = useRoute()
const pid = Number(route.params.id)
const loading = ref(false)
const markdown = ref('')

const rendered = computed(() => marked.parse(markdown.value || '') as string)

async function load() {
  loading.value = true
  try {
    const res = await getReport(pid)
    markdown.value = res.markdown || '暂无报告'
  } finally { loading.value = false }
}

function exportMd() {
  const blob = new Blob([markdown.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `security-report-${pid}.md`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.markdown-body { line-height: 1.8; }
.markdown-body :deep(h1) { font-size: 28px; border-bottom: 2px solid #eee; padding-bottom: 8px; }
.markdown-body :deep(h2) { font-size: 24px; margin-top: 24px; }
.markdown-body :deep(h3) { font-size: 20px; margin-top: 16px; }
.markdown-body :deep(code) { background: #f5f7fa; padding: 2px 6px; border-radius: 3px; }
.markdown-body :deep(pre) { background: #282c34; color: #abb2bf; padding: 12px; border-radius: 4px; overflow-x: auto; }
.markdown-body :deep(table) { border-collapse: collapse; width: 100%; margin: 12px 0; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid #ddd; padding: 8px; }
</style>
