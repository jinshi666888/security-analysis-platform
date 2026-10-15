<template>
  <div>
    <el-button type="primary" @click="load">刷新基准报告</el-button>
    <el-empty v-if="!report.aggregate" description="暂无基准数据，请先执行 benchmark 命令" />
    <div v-else>
      <el-row :gutter="16" class="cards">
        <el-col :span="6"><el-card><div class="num">{{ report.aggregate.projects }}</div><div>基准项目数</div></el-card></el-col>
        <el-col :span="6"><el-card><div class="num">{{ report.aggregate.total_findings }}</div><div>总检出</div></el-card></el-col>
        <el-col :span="6"><el-card><div class="num">{{ pct(report.aggregate.precision) }}</div><div>Precision</div></el-card></el-col>
        <el-col :span="6"><el-card><div class="num">{{ pct(report.aggregate.recall) }}</div><div>Recall</div></el-card></el-col>
      </el-row>
      <el-row :gutter="16" class="cards">
        <el-col :span="6"><el-card><div class="num">{{ pct(report.aggregate.false_positive_rate) }}</div><div>FP Rate</div></el-card></el-col>
        <el-col :span="6"><el-card><div class="num">{{ pct(report.aggregate.confirmed_rate) }}</div><div>Confirmed Rate</div></el-card></el-col>
      </el-row>

      <el-card style="margin-top:16px">
        <template #header>分项结果</template>
        <el-table :data="report.projects || []">
          <el-table-column prop="project" label="项目" />
          <el-table-column prop="scale" label="规模" width="100" />
          <el-table-column prop="metrics.true_positives" label="TP" width="80" />
          <el-table-column prop="metrics.false_positives" label="FP" width="80" />
          <el-table-column prop="metrics.false_negatives" label="FN" width="80" />
          <el-table-column label="Precision" width="100">
            <template #default="{ row }">{{ pct(row.metrics.precision) }}</template>
          </el-table-column>
          <el-table-column label="Recall" width="100">
            <template #default="{ row }">{{ pct(row.metrics.recall) }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getBenchmark } from '@/api'

const route = useRoute()
const pid = Number(route.params.id)
const report = ref<any>({})

async function load() { report.value = await getBenchmark(pid) }

function pct(v: any) {
  if (v === null || v === undefined) return '-'
  return (Number(v) * 100).toFixed(1) + '%'
}

onMounted(load)
</script>

<style scoped>
.cards { margin: 16px 0; }
.num { font-size: 32px; font-weight: bold; color: #409eff; }
</style>
