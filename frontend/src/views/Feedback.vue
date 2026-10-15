<template>
  <div>
    <el-button type="primary" @click="load">刷新规则</el-button>
    <el-empty v-if="!rules.length" description="暂无误报规则，请先在复核中标记 false_positive" />
    <el-table v-else :data="rules" style="margin-top:16px">
      <el-table-column prop="id" label="规则 ID" width="200" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="occurrences" label="命中次数" width="100" />
      <el-table-column label="自动抑制" width="100">
        <template #default="{ row }">
          <el-tag :type="row.auto_suppress ? 'success' : 'info'">
            {{ row.auto_suppress ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="匹配条件">
        <template #default="{ row }">
          {{ row.match?.source }} / {{ row.match?.tool_ref }} @ {{ row.match?.file_pattern }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getFeedbackRules } from '@/api'

const route = useRoute()
const pid = Number(route.params.id)
const rules = ref<any[]>([])

async function load() { rules.value = await getFeedbackRules(pid) }

onMounted(load)
</script>
