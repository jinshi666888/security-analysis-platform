<template>
  <div>
    <el-row :gutter="12" class="stats">
      <el-col :span="8"><el-card><div class="num">{{ stats.total }}</div><div class="lbl">提交总数</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="num">{{ stats.accepted || 0 }}</div><div class="lbl">已通过</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="num">¥{{ stats.reward_total || 0 }}</div><div class="lbl">已确认赏金</div></el-card></el-col>
    </el-row>

    <el-card class="filter">
      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width:130px" @change="reload">
            <el-option v-for="s in statuses" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="平台">
          <el-input v-model="filters.platform" clearable placeholder="平台" style="width:150px" />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" clearable placeholder="标题" style="width:180px" />
        </el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button type="success" @click="openCreate">手工登记提交</el-button>
      </el-form>
    </el-card>

    <el-table :data="items" style="margin-top:16px" height="480">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip />
      <el-table-column prop="platform" label="平台" width="110" />
      <el-table-column prop="severity" label="等级" width="90" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }"><el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="赏金" width="100">
        <template #default="{ row }">{{ row.reward_amount ? '¥' + row.reward_amount : '-' }}</template>
      </el-table-column>
      <el-table-column prop="finding_id" label="关联漏洞" width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.finding_id || '-' }}</template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="180" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openTimeline(row)">进度</el-button>
          <el-button size="small" type="primary" @click="openUpdate(row)">更新</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
                   @current-change="load" layout="total, prev, pager, next" />

    <el-dialog v-model="createVisible" title="手工登记 SRC 提交" width="640px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="平台"><el-input v-model="form.platform" /></el-form-item>
        <el-form-item label="等级">
          <el-select v-model="form.severity">
            <el-option v-for="s in ['critical','high','medium','low','info']" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联任务">
          <el-select v-model="form.task_id" clearable filterable placeholder="可选" style="width:320px">
            <el-option v-for="t in tasks" :key="t.id" :label="`#${t.id} [${t.platform}] ${t.title}`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联项目"><el-input-number v-model="form.project_id" :min="0" /></el-form-item>
        <el-form-item label="关联漏洞ID"><el-input v-model="form.finding_id" placeholder="可选，本地 finding id" /></el-form-item>
        <el-form-item label="资产/文件"><el-input v-model="form.asset" /></el-form-item>
        <el-form-item label="漏洞类型"><el-input v-model="form.vuln_type" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="updateVisible" title="更新提交进度" width="560px">
      <el-form :model="updateForm" label-width="110px">
        <el-form-item label="状态">
          <el-select v-model="updateForm.status">
            <el-option v-for="s in statuses" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="赏金金额">
          <el-input-number v-model="updateForm.reward_amount" :min="0" :precision="2" />
          <span class="hint">通过/发放时自动计入收益</span>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="updateForm.note" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="updateVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpdate">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="timelineVisible" title="提交进度时间线" size="420px">
      <el-timeline>
        <el-timeline-item v-for="(t, i) in current.timeline || []" :key="i" :timestamp="t.time"
                          :type="statusTag(t.status)">
          <b>{{ statusText(t.status) }}</b><div>{{ t.note }}</div>
        </el-timeline-item>
      </el-timeline>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listSubmissions, submissionStats, createSubmission, updateSubmission, listSrcTasks } from '@/api'

const items = ref<any[]>([])
const tasks = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const stats = ref<any>({})
const statuses = [
  { value: 'draft', label: '草稿' }, { value: 'submitted', label: '已提交' },
  { value: 'reviewing', label: '审核中' }, { value: 'accepted', label: '已通过' },
  { value: 'rejected', label: '已驳回' }, { value: 'duplicate', label: '重复' },
  { value: 'paid', label: '已发放' },
]
const filters = reactive({ status: '', platform: '', keyword: '' })

const createVisible = ref(false)
const form = reactive({ title: '', platform: '', severity: 'medium', task_id: undefined as number | undefined, project_id: 0, finding_id: '', asset: '', vuln_type: '', note: '' })
const updateVisible = ref(false)
const updateForm = reactive({ id: 0, status: '', reward_amount: 0, note: '' })
const timelineVisible = ref(false)
const current = ref<any>({})

function statusTag(s: string) {
  return { draft: 'info', submitted: '', reviewing: 'warning', accepted: 'success', paid: 'success', rejected: 'danger', duplicate: 'info' }[s] || ''
}
function statusText(s: string) { return statuses.find(x => x.value === s)?.label || s }

async function load() {
  const res = await listSubmissions({ ...filters, limit: pageSize, offset: (page.value - 1) * pageSize })
  items.value = res.items
  total.value = res.total
  stats.value = await submissionStats()
}
function reload() { page.value = 1; load() }

async function openCreate() {
  Object.assign(form, { title: '', platform: '', severity: 'medium', task_id: undefined, project_id: 0, finding_id: '', asset: '', vuln_type: '', note: '' })
  const res = await listSrcTasks({ limit: 200, offset: 0 })
  tasks.value = res.items
  createVisible.value = true
}
async function submit() {
  if (!form.title.trim()) { ElMessage.warning('标题必填'); return }
  const payload: any = { ...form }
  if (!payload.task_id) delete payload.task_id
  if (!payload.project_id) delete payload.project_id
  await createSubmission(payload)
  createVisible.value = false
  ElMessage.success('已登记提交')
  reload()
}

function openUpdate(row: any) {
  Object.assign(updateForm, { id: row.id, status: row.status, reward_amount: row.reward_amount, note: '' })
  updateVisible.value = true
}
async function submitUpdate() {
  await updateSubmission(updateForm.id, { status: updateForm.status, reward_amount: updateForm.reward_amount, note: updateForm.note })
  updateVisible.value = false
  ElMessage.success('已更新')
  reload()
}

function openTimeline(row: any) { current.value = row; timelineVisible.value = true }

onMounted(load)
</script>

<style scoped>
.stats { margin-bottom: 12px; }
.stats .num { font-size: 26px; font-weight: bold; }
.stats .lbl { color: #888; font-size: 14px; }
.filter { margin-bottom: 8px; }
.hint { color: #999; font-size: 14px; margin-left: 8px; }
</style>
