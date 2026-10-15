<template>
  <div>
    <el-row :gutter="12" class="cards">
      <el-col :span="6"><el-card><div class="num">¥{{ summary.total || 0 }}</div><div class="lbl">累计收益</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="num warn">¥{{ summary.pending || 0 }}</div><div class="lbl">待结算</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="num ok">¥{{ summary.withdrawable || 0 }}</div><div class="lbl">可提现</div></el-card></el-col>
      <el-col :span="6"><el-card><div class="num">¥{{ summary.withdrawn || 0 }}</div><div class="lbl">已提现</div></el-card></el-col>
    </el-row>

    <el-row :gutter="16" class="charts">
      <el-col :span="12"><el-card><div ref="platformPie" style="height:300px"></div></el-card></el-col>
      <el-col :span="12"><el-card><div ref="monthBar" style="height:300px"></div></el-card></el-col>
    </el-row>

    <el-card class="filter">
      <el-form inline>
        <el-form-item label="平台">
          <el-input v-model="filters.platform" clearable placeholder="平台" style="width:150px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width:140px">
            <el-option label="待结算" value="pending" />
            <el-option label="可提现" value="available" />
            <el-option label="已提现" value="withdrawn" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button @click="openAdd">手工补录收益</el-button>
        <el-button type="success" @click="router.push('/withdrawals')">去提现</el-button>
      </el-form>
    </el-card>

    <el-table :data="items" style="margin-top:16px" height="360">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="created_at" label="入账时间" width="180" />
      <el-table-column prop="platform" label="平台" width="140" />
      <el-table-column label="金额" width="120">
        <template #default="{ row }">¥{{ row.amount }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }"><el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="submission_id" label="来源提交" width="110">
        <template #default="{ row }">{{ row.submission_id ? '#' + row.submission_id : '-' }}</template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" show-overflow-tooltip />
    </el-table>
    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
                   @current-change="load" layout="total, prev, pager, next" />

    <el-dialog v-model="addVisible" title="手工补录收益" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="平台"><el-input v-model="form.platform" /></el-form-item>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="待结算" value="pending" />
            <el-option label="可提现" value="available" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, reactive, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { listEarnings, earningSummary, createEarning } from '@/api'

const router = useRouter()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const summary = reactive<any>({})
const filters = reactive({ platform: '', status: '' })
const platformPie = ref<HTMLElement>()
const monthBar = ref<HTMLElement>()
const charts: Record<string, echarts.ECharts> = {}
const addVisible = ref(false)
const form = reactive({ platform: '', amount: 0, status: 'available', remark: '' })

const statusMap: Record<string, string> = { pending: '待结算', available: '可提现', withdrawn: '已提现' }
function statusTag(s: string) { return { pending: 'warning', available: 'success', withdrawn: 'info' }[s] || '' }
function statusText(s: string) { return statusMap[s] || s }

function chart(key: string, el?: HTMLElement) {
  if (!el) return null
  if (!charts[key]) charts[key] = echarts.init(el)
  return charts[key]
}

async function load() {
  const res = await listEarnings({ ...filters, limit: pageSize, offset: (page.value - 1) * pageSize })
  items.value = res.items
  total.value = res.total
  Object.assign(summary, await earningSummary())
  await nextTick()
  renderCharts()
}

function renderCharts() {
  const pie = chart('platform', platformPie.value)
  pie?.setOption({
    title: { text: '平台收益占比' }, tooltip: {},
    series: [{ type: 'pie', radius: ['40%', '70%'],
      data: Object.entries(summary.by_platform || {}).map(([name, value]) => ({ name, value })) }]
  }, true)

  const bar = chart('month', monthBar.value)
  const entries = Object.entries(summary.by_month || {})
  bar?.setOption({
    title: { text: '月度收益趋势' }, tooltip: {},
    xAxis: { type: 'category', data: entries.map(e => e[0]) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: entries.map(e => e[1]) }]
  }, true)
}

function reload() { page.value = 1; load() }
function openAdd() { Object.assign(form, { platform: '', amount: 0, status: 'available', remark: '' }); addVisible.value = true }
async function submit() {
  await createEarning({ ...form })
  addVisible.value = false
  ElMessage.success('已补录')
  reload()
}

function onResize() { Object.values(charts).forEach(c => c.resize()) }
onMounted(() => { window.addEventListener('resize', onResize); load() })
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  Object.values(charts).forEach(c => c.dispose())
  for (const k of Object.keys(charts)) delete charts[k]
})
</script>

<style scoped>
.cards { margin-bottom: 12px; }
.cards .num { font-size: 28px; font-weight: bold; }
.cards .num.warn { color: #e6a23c; }
.cards .num.ok { color: #67c23a; }
.cards .lbl { color: #888; font-size: 14px; }
.charts { margin-bottom: 16px; }
.filter { margin-bottom: 8px; }
</style>
