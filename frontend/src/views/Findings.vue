<template>
  <div>
    <el-card class="filter">
      <el-form inline>
        <el-form-item label="严重级">
          <el-select v-model="filters.severity" clearable style="width:120px">
            <el-option v-for="s in ['critical','high','medium','low','info']" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable style="width:140px">
            <el-option v-for="s in ['triaged','confirmed','false_positive','accepted_risk','needs_review']" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input v-model="filters.keyword" clearable placeholder="文件/证据/ID" style="width:200px" />
        </el-form-item>
        <el-button type="primary" @click="page = 1; load()">查询</el-button>
      </el-form>
    </el-card>

    <el-table :data="items" style="margin-top:16px" @row-click="openDetail" height="560">
      <el-table-column prop="id" label="ID" width="90" fixed />
      <el-table-column prop="severity" label="严重级" width="100">
        <template #default="{ row }"><el-tag :type="sevTag(row.severity)">{{ row.severity }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="160" />
      <el-table-column prop="file" label="文件" min-width="220" show-overflow-tooltip />
      <el-table-column prop="line" label="行号" width="70" />
      <el-table-column prop="status" label="状态" width="130" />
      <el-table-column prop="cwe" label="CWE" width="90" />
      <el-table-column prop="cvss_score" label="CVSS" width="80" />
      <el-table-column prop="confidence" label="置信度" width="90" />
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize"
                   :total="total" @current-change="load" layout="total, prev, pager, next" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listFindings } from '@/api'

const route = useRoute()
const router = useRouter()
const pid = Number(route.params.id)
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const filters = reactive({ severity: '', status: '', keyword: '' })

async function load() {
  const res = await listFindings(pid, { ...filters, page: page.value, page_size: pageSize.value })
  items.value = res.items
  total.value = res.total
}

function sevTag(s: string) {
  return { critical: 'danger', high: 'warning', medium: '', low: 'info', info: 'info' }[s] || ''
}

function openDetail(row: any) {
  router.push(`/projects/${pid}/findings/${row.id}`)
}

onMounted(load)
</script>
