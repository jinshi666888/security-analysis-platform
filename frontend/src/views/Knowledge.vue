<template>
  <div>
    <el-tabs v-model="tab" class="tabs">
      <el-tab-pane label="漏洞知识库" name="kb">
        <el-card class="filter">
          <el-form inline>
            <el-form-item label="分类">
              <el-select v-model="category" clearable placeholder="全部" style="width:150px" @change="loadArticles">
                <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
            <el-form-item label="搜索">
              <el-input v-model="keyword" clearable placeholder="漏洞名称 / CWE / 关键词" style="width:240px" />
            </el-form-item>
            <el-button type="primary" @click="loadArticles">查询</el-button>
          </el-form>
        </el-card>

        <el-collapse v-model="activeArticle" class="collapse">
          <el-collapse-item v-for="a in articles" :key="a.id" :name="a.id">
            <template #title>
              <span class="art-title">{{ a.title }}</span>
              <el-tag size="small" class="ml8">{{ a.category }}</el-tag>
              <el-tag size="small" type="warning" class="ml8">{{ a.cwe }}</el-tag>
              <el-tag size="small" :type="sevTag(a.severity)" class="ml8">{{ a.severity }}</el-tag>
            </template>
            <div class="summary">{{ a.summary }}</div>
            <pre class="detail">{{ a.detail }}</pre>
          </el-collapse-item>
        </el-collapse>
      </el-tab-pane>

      <el-tab-pane label="提交规范指引" name="guide">
        <el-card v-for="(s, i) in guidelines.sections || []" :key="i" class="section">
          <h3>{{ s.heading }}</h3>
          <pre class="detail">{{ s.body }}</pre>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="合规风险提示" name="compliance">
        <el-alert type="warning" :closable="false" class="scope"
                  :title="'授权范围声明：' + (compliance.authorization_scope || '')" />
        <el-card v-for="(s, i) in compliance.sections || []" :key="i" class="section">
          <h3>{{ s.heading }}</h3>
          <pre class="detail">{{ s.body }}</pre>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { kbArticles, kbGuidelines, kbCompliance } from '@/api'

const tab = ref('kb')
const articles = ref<any[]>([])
const categories = ref<string[]>([])
const category = ref('')
const keyword = ref('')
const activeArticle = ref<string[]>([])
const guidelines = ref<any>({})
const compliance = ref<any>({})

function sevTag(s: string) { return { critical: 'danger', high: 'warning', medium: '', low: 'info', info: 'info' }[s] || '' }

async function loadArticles() {
  const res = await kbArticles({ category: category.value || undefined, keyword: keyword.value || undefined })
  articles.value = res.items
  categories.value = res.categories || []
}

onMounted(async () => {
  await loadArticles()
  guidelines.value = await kbGuidelines()
  compliance.value = await kbCompliance()
})
</script>

<style scoped>
.tabs { background: #fff; padding: 8px 16px; border-radius: 4px; }
.filter { margin-bottom: 8px; }
.collapse { border-top: none; }
.art-title { font-weight: 600; }
.ml8 { margin-left: 8px; }
.summary { color: #606266; margin-bottom: 8px; }
.detail { white-space: pre-wrap; font-family: inherit; font-size: 15px; line-height: 1.7; color: #303133; background: #fafafa; padding: 12px; border-radius: 4px; }
.section { margin-bottom: 12px; }
.section h3 { margin: 0 0 8px; font-size: 17px; }
.scope { margin-bottom: 12px; }
</style>
