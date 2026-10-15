<template>
  <div>
    <el-card class="filter">
      <el-form inline>
        <el-form-item label="分类">
          <el-select v-model="filters.category" clearable placeholder="全部" style="width:150px" @change="reload">
            <el-option label="收益" value="earning" />
            <el-option label="提现" value="withdrawal" />
            <el-option label="提交" value="submission" />
            <el-option label="系统" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="filters.unreadOnly" @change="reload">只看未读</el-checkbox>
        </el-form-item>
        <el-button type="primary" @click="reload">刷新</el-button>
        <el-button @click="readAll">全部标记已读</el-button>
      </el-form>
    </el-card>

    <el-table :data="items" style="margin-top:16px" height="520" :row-class-name="rowClass">
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_read ? 'info' : 'danger'" size="small">{{ row.is_read ? '已读' : '未读' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="110">
        <template #default="{ row }">{{ categoryText(row.category) }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" width="220" />
      <el-table-column prop="content" label="内容" min-width="280" show-overflow-tooltip />
      <el-table-column prop="created_at" label="时间" width="180" />
      <el-table-column label="操作" width="110">
        <template #default="{ row }">
          <el-button v-if="!row.is_read" size="small" @click="markRead(row)">标记已读</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
                   @current-change="load" layout="total, prev, pager, next" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listNotifications, readNotification, readAllNotifications } from '@/api'

const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const filters = reactive({ category: '', unreadOnly: false })

const categoryMap: Record<string, string> = { earning: '收益', withdrawal: '提现', submission: '提交', system: '系统' }
function categoryText(c: string) { return categoryMap[c] || c }
function rowClass({ row }: any) { return row.is_read ? '' : 'unread-row' }

async function load() {
  const res = await listNotifications({ category: filters.category || undefined, unread_only: filters.unreadOnly, limit: pageSize, offset: (page.value - 1) * pageSize })
  items.value = res.items
  total.value = res.total
}
function reload() { page.value = 1; load() }

async function markRead(row: any) { await readNotification(row.id); load() }
async function readAll() { await readAllNotifications(); ElMessage.success('已全部标记'); load() }

onMounted(load)
</script>

<style scoped>
.filter { margin-bottom: 8px; }
:deep(.unread-row) { font-weight: 500; background: #fdf6ec; }
</style>
