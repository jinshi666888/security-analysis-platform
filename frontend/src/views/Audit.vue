<template>
  <div>
    <el-card class="filter">
      <el-form inline>
        <el-form-item label="操作类型">
          <el-select v-model="action" clearable placeholder="全部" style="width:200px" @change="reload">
            <el-option v-for="a in actions" :key="a" :label="a" :value="a" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="reload">刷新</el-button>
      </el-form>
    </el-card>

    <el-table :data="items" style="margin-top:16px" height="560">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="created_at" label="时间" width="200" />
      <el-table-column prop="username" label="操作人" width="140" />
      <el-table-column prop="action" label="操作" width="180" />
      <el-table-column prop="target" label="对象" width="200" show-overflow-tooltip />
      <el-table-column prop="detail" label="详情" show-overflow-tooltip />
    </el-table>

    <el-pagination v-model:current-page="page" :page-size="pageSize"
                   :total="total" @current-change="load"
                   layout="total, prev, pager, next" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listAudit } from '@/api'

const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const action = ref('')
const actions = [
  'auth.login', 'auth.login.failed', 'project.create', 'project.delete',
  'scan.trigger', 'review.apply', 'user.create', 'user.update', 'user.delete',
]

async function load() {
  const res = await listAudit({
    action: action.value || undefined,
    limit: pageSize,
    offset: (page.value - 1) * pageSize,
  })
  items.value = res.items
  total.value = res.total
}

function reload() { page.value = 1; load() }

onMounted(load)
</script>

<style scoped>
.filter { margin-bottom: 8px; }
</style>
