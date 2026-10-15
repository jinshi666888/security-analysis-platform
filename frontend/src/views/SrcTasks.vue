<template>
  <div>
    <el-row :gutter="12" class="stats">
      <el-col :span="6"><el-card><div class="num">{{ stats.total }}</div><div class="lbl">任务总数</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="num">{{ stats.by_status?.open || 0 }}</div><div class="lbl">招募中</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="num">¥{{ stats.reward_max_total || 0 }}</div><div class="lbl">赏金上限合计</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="num">{{ platformCount }}</div><div class="lbl">覆盖平台数</div></el-card></el-col>
    </el-row>

    <el-card class="filter">
      <el-form inline>
        <el-form-item label="平台">
          <el-select v-model="filters.platform" clearable placeholder="全部" style="width:150px" @change="reload">
            <el-option v-for="p in platforms" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width:130px" @change="reload">
            <el-option v-for="s in statuses" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" clearable placeholder="任务标题" style="width:200px" />
        </el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button type="success" @click="openCreate">手工登记</el-button>
        <el-button @click="importVisible = true">批量导入</el-button>
      </el-form>
    </el-card>

    <el-table :data="items" style="margin-top:16px" height="480">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="platform" label="平台" width="120" />
      <el-table-column prop="title" label="任务标题" min-width="240" show-overflow-tooltip />
      <el-table-column label="赏金区间" width="160">
        <template #default="{ row }">{{ row.currency }} {{ row.reward_min }} ~ {{ row.reward_max }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }"><el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="scope" label="授权范围" min-width="180" show-overflow-tooltip />
      <el-table-column prop="source" label="来源" width="90" />
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="操作" width="80">
        <template #default="{ row }">
          <el-button v-if="auth.role === 'admin'" size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
                   @current-change="load" layout="total, prev, pager, next" />

    <el-dialog v-model="createVisible" title="手工登记 SRC 任务" width="640px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="平台"><el-input v-model="form.platform" /></el-form-item>
        <el-form-item label="任务标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option v-for="s in statuses" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="赏金区间">
          <el-input-number v-model="form.reward_min" :min="0" /> ~
          <el-input-number v-model="form.reward_max" :min="0" />
          <el-select v-model="form.currency" style="width:100px;margin-left:8px">
            <el-option label="CNY" value="CNY" /><el-option label="USD" value="USD" />
          </el-select>
        </el-form-item>
        <el-form-item label="授权范围"><el-input v-model="form.scope" placeholder="授权域名/IP/App，用于合规自检" /></el-form-item>
        <el-form-item label="任务链接"><el-input v-model="form.url" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importVisible" title="批量导入任务（CSV / JSON）" width="640px">
      <el-alert type="info" :closable="false" class="tip"
                title="CSV 表头：platform,title,status,reward_min,reward_max,currency,scope,url,description,deadline" />
      <el-radio-group v-model="importForm.format" style="margin:8px 0">
        <el-radio-button label="csv" value="csv">CSV</el-radio-button>
        <el-radio-button label="json" value="json">JSON</el-radio-button>
      </el-radio-group>
      <el-input v-model="importForm.content" type="textarea" :rows="12"
                :placeholder="importPlaceholder" />
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" @click="doImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { listSrcTasks, srcTaskStats, createSrcTask, importSrcTasks, deleteSrcTask } from '@/api'

const auth = useAuthStore()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const stats = ref<any>({})
// 平台筛选项动态来自任务数据，避免硬编码遗漏
const platforms = computed(() => Object.keys(stats.value.by_platform || {}).sort())
const statuses = [
  { value: 'open', label: '招募中' }, { value: 'in_progress', label: '进行中' },
  { value: 'submitted', label: '已提交' }, { value: 'closed', label: '已结束' },
]
const filters = reactive({ platform: '', status: '', keyword: '' })
const platformCount = computed(() => Object.keys(stats.value.by_platform || {}).length)

const createVisible = ref(false)
const form = reactive({ platform: '', title: '', status: 'open', reward_min: 0, reward_max: 0, currency: 'CNY', scope: '', url: '', description: '' })
const importVisible = ref(false)
const importForm = reactive({ format: 'csv', content: '' })
const importPlaceholder = computed(() => importForm.format === 'csv'
  ? 'platform,title,reward_min,reward_max\n补天,某活动众测,500,5000'
  : '{ "items": [ { "platform": "补天", "title": "某活动众测", "reward_max": 5000 } ] }')

function statusTag(s: string) {
  return { open: 'success', in_progress: 'warning', submitted: '', closed: 'info' }[s] || ''
}
function statusText(s: string) {
  return statuses.find(x => x.value === s)?.label || s
}

async function load() {
  const res = await listSrcTasks({ ...filters, limit: pageSize, offset: (page.value - 1) * pageSize })
  items.value = res.items
  total.value = res.total
  stats.value = await srcTaskStats()
}
function reload() { page.value = 1; load() }

function openCreate() {
  Object.assign(form, { platform: '', title: '', status: 'open', reward_min: 0, reward_max: 0, currency: 'CNY', scope: '', url: '', description: '' })
  createVisible.value = true
}
async function submit() {
  if (!form.title.trim() || !form.platform.trim()) { ElMessage.warning('平台与标题必填'); return }
  await createSrcTask({ ...form })
  createVisible.value = false
  ElMessage.success('已登记')
  reload()
}
async function doImport() {
  if (!importForm.content.trim()) { ElMessage.warning('请粘贴内容'); return }
  const res = await importSrcTasks({ ...importForm })
  ElMessage.success(`导入 ${res.imported} 条，跳过 ${res.skipped} 条`)
  importVisible.value = false
  importForm.content = ''
  reload()
}
async function onDelete(row: any) {
  await deleteSrcTask(row.id)
  ElMessage.success('已删除')
  reload()
}

onMounted(load)
</script>

<style scoped>
.stats { margin-bottom: 12px; }
.stats .num { font-size: 26px; font-weight: bold; }
.stats .lbl { color: #888; font-size: 14px; }
.filter { margin-bottom: 8px; }
.tip { margin-bottom: 8px; }
</style>
