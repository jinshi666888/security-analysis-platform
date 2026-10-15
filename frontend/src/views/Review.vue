<template>
  <div>
    <el-button type="primary" @click="load">刷新待复核</el-button>
    <el-table :data="pending" @selection-change="onSelect" style="margin-top:16px">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="90" />
      <el-table-column prop="severity" label="严重级" width="100">
        <template #default="{ row }"><el-tag :type="sevTag(row.severity)">{{ row.severity }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="type" label="类型" />
      <el-table-column prop="file" label="文件" show-overflow-tooltip />
      <el-table-column prop="line" label="行号" width="70" />
      <el-table-column prop="status" label="状态" />
    </el-table>

    <el-card style="margin-top:16px">
      <el-form inline>
        <el-form-item label="决策">
          <el-select v-model="decision" style="width:180px">
            <el-option label="确认漏洞 confirmed" value="confirmed" />
            <el-option label="误报 false_positive" value="false_positive" />
            <el-option label="接受风险 accepted_risk" value="accepted_risk" />
            <el-option label="需复核 needs_review" value="needs_review" />
          </el-select>
        </el-form-item>
        <el-form-item label="复核人"><el-input v-model="reviewer" style="width:140px" /></el-form-item>
        <el-button type="primary" :disabled="!selected.length" @click="submit">批量提交 ({{ selected.length }})</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { pendingReview, applyReview } from '@/api'

const route = useRoute()
const pid = Number(route.params.id)
const pending = ref<any[]>([])
const selected = ref<any[]>([])
const decision = ref('confirmed')
const reviewer = ref('analyst')

async function load() { pending.value = await pendingReview(pid) }

function onSelect(rows: any[]) { selected.value = rows }

async function submit() {
  const items = selected.value.map(r => ({ finding_id: r.id, decision: decision.value }))
  await applyReview(pid, { items, reviewer: reviewer.value })
  ElMessage.success('复核已提交')
  load()
}

function sevTag(s: string) {
  return { critical: 'danger', high: 'warning', medium: '', low: 'info', info: 'info' }[s] || ''
}

onMounted(load)
</script>
