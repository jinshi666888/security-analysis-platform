<template>
  <div>
    <el-select v-model="projectId" placeholder="选择项目" style="width:240px">
      <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
    </el-select>

    <el-row :gutter="16" class="cards">
      <el-col :span="4"><el-card><div class="stat-num">{{ stats.total_findings }}</div><div>总漏洞</div></el-card></el-col>
      <el-col :span="4"><el-card><div class="stat-num critical">{{ stats.by_severity?.critical || 0 }}</div><div>Critical</div></el-card></el-col>
      <el-col :span="4"><el-card><div class="stat-num high">{{ stats.by_severity?.high || 0 }}</div><div>High</div></el-card></el-col>
      <el-col :span="4"><el-card><div class="stat-num medium">{{ stats.by_severity?.medium || 0 }}</div><div>Medium</div></el-card></el-col>
      <el-col :span="4"><el-card><div class="stat-num">{{ stats.review_count || 0 }}</div><div>已复核</div></el-card></el-col>
      <el-col :span="4">
        <el-card>
          <div class="stat-num" :class="stats.gate?.passed ? 'ok' : 'bad'">
            {{ stats.gate?.passed ? 'PASS' : 'BLOCK' }}
          </div>
          <div>CI 门禁</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts">
      <el-col :span="12"><el-card><div ref="sevPie" style="height:320px"></div></el-card></el-col>
      <el-col :span="12"><el-card><div ref="cweBar" style="height:320px"></div></el-card></el-col>
    </el-row>
    <el-row :gutter="16" class="charts">
      <el-col :span="12"><el-card><div ref="owaspRadar" style="height:320px"></div></el-card></el-col>
      <el-col :span="12"><el-card><div ref="sourceBar" style="height:320px"></div></el-card></el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, reactive, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { listProjects, dashboardStats } from '@/api'

const projects = ref<any[]>([])
const projectId = ref<number | null>(null)
const stats = reactive<any>({})
const sevPie = ref<HTMLElement>()
const cweBar = ref<HTMLElement>()
const owaspRadar = ref<HTMLElement>()
const sourceBar = ref<HTMLElement>()

// 复用图表实例，避免重复 echarts.init 造成实例泄漏
const charts: Record<string, echarts.ECharts> = {}

function chart(key: string, el?: HTMLElement): echarts.ECharts | null {
  if (!el) return null
  if (!charts[key]) charts[key] = echarts.init(el)
  return charts[key]
}

async function load() {
  if (!projectId.value) return
  const data = await dashboardStats(projectId.value)
  Object.assign(stats, data)
  await nextTick()
  renderCharts()
}

function renderCharts() {
  const pie = chart('sevPie', sevPie.value)
  pie?.setOption({
    title: { text: '严重级分布' },
    tooltip: {},
    series: [{ type: 'pie', radius: ['40%', '70%'],
      data: Object.entries(stats.by_severity || {}).map(([name, value]) => ({ name, value })) }]
  }, true)

  const bar = chart('cweBar', cweBar.value)
  const entries = Object.entries(stats.by_cwe || {})
  bar?.setOption({
    title: { text: 'Top CWE' },
    tooltip: {},
    xAxis: { type: 'category', data: entries.map(e => e[0]) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: entries.map(e => e[1]) }]
  }, true)

  const radar = chart('owaspRadar', owaspRadar.value)
  const owasp = stats.by_owasp || {}
  const indicators = ['A01','A02','A03','A04','A05','A06','A07','A08','A09','A10'].map(n => ({ name: n, max: 20 }))
  radar?.setOption({
    title: { text: 'OWASP Top 10 分布' },
    tooltip: {},
    radar: { indicator: indicators },
    series: [{ type: 'radar', data: [{ value: indicators.map(i => owasp[i.name] || 0), name: '数量' }] }]
  }, true)

  const src = chart('sourceBar', sourceBar.value)
  const srcEntries = Object.entries(stats.by_source || {})
  src?.setOption({
    title: { text: '扫描器来源分布' },
    tooltip: {},
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: srcEntries.map(e => e[0]) },
    series: [{ type: 'bar', data: srcEntries.map(e => e[1]) }]
  }, true)
}

function onResize() { Object.values(charts).forEach(c => c.resize()) }

onMounted(async () => {
  window.addEventListener('resize', onResize)
  projects.value = await listProjects()
  if (projects.value[0]) projectId.value = projects.value[0].id
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  Object.values(charts).forEach(c => c.dispose())
  for (const k of Object.keys(charts)) delete charts[k]
})

watch(projectId, load)
</script>

<style scoped>
.cards { margin: 16px 0; }
.stat-num { font-size: 32px; font-weight: bold; }
.stat-num.critical { color: #f56c6c; }
.stat-num.high { color: #e6a23c; }
.stat-num.medium { color: #f0c78a; }
.stat-num.ok { color: #67c23a; }
.stat-num.bad { color: #f56c6c; }
.charts { margin-bottom: 16px; }
</style>
