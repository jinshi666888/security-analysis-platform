<template>
  <div ref="chartRef" style="width:100%;height:400px"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{ taintPath: any[] }>()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function render() {
  if (!chartRef.value || !props.taintPath?.length) return
  if (!chart) chart = echarts.init(chartRef.value)
  const nodes = props.taintPath.map((hop, idx) => ({
    id: `n${idx}`,
    name: `${idx === 0 ? 'SOURCE' : idx === props.taintPath.length - 1 ? 'SINK' : 'P' + idx}\n${hop.file?.split('/').pop()}:${hop.lines}`,
    symbolSize: 60,
    itemStyle: { color: idx === 0 ? '#f56c6c' : idx === props.taintPath.length - 1 ? '#e6a23c' : '#409eff' },
    label: { show: true, fontSize: 13 },
    code: hop.code,
  }))
  const edges = props.taintPath.slice(0, -1).map((_, i) => ({
    source: `n${i}`, target: `n${i + 1}`,
    label: { show: true, formatter: props.taintPath[i + 1].transform || '', fontSize: 12 },
  }))
  chart.setOption({
    tooltip: { formatter: (p: any) => p.data.code || '' },
    series: [{
      type: 'graph', layout: 'force', roam: true, data: nodes, links: edges,
      edgeSymbol: ['none', 'arrow'], edgeSymbolSize: 8,
      force: { repulsion: 300, edgeLength: 120 },
      lineStyle: { color: '#999', width: 2 },
      label: { color: '#fff' },
    }],
  })
}

onMounted(async () => { await nextTick(); render() })
watch(() => props.taintPath, render)
</script>
