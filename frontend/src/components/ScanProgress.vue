<template>
  <el-dialog v-model="visible" title="扫描进度" width="500px" :close-on-click-modal="false" :show-close="false">
    <el-steps :active="currentStep" finish-status="success" align-center>
      <el-step v-for="s in stages" :key="s" :title="s" :status="stepStatus(s)" />
    </el-steps>
    <div style="margin-top:20px;text-align:center">
      <el-progress :percentage="Math.round(progress * 100)" />
      <p style="color:#666">{{ statusText }}</p>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{ projectId: number | null }>()
const emit = defineEmits(['done'])

const visible = ref(false)
const stages = ['inventory', 'scan', 'normalize', 'context', 'taint', 'triage', 'output']
const stageStatusMap = ref<Record<string, string>>({})
const progress = ref(0)
let ws: WebSocket | null = null

const currentStep = computed(() => {
  const doneCount = stages.filter(s => stageStatusMap.value[s] === 'done').length
  return doneCount
})

const statusText = computed(() => {
  const running = stages.find(s => stageStatusMap.value[s] === 'running')
  if (running) return `正在执行: ${running}...`
  if (progress.value >= 1) return '扫描完成'
  return '等待中...'
})

function stepStatus(s: string) {
  return stageStatusMap.value[s] === 'done' ? 'success'
    : stageStatusMap.value[s] === 'running' ? 'process' : ''
}

function connect() {
  if (!props.projectId) return
  visible.value = true
  stageStatusMap.value = {}
  progress.value = 0
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${proto}//${location.host}/ws/scan/${props.projectId}`)
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.stage && data.status) {
      stageStatusMap.value[data.stage] = data.status
      if (data.progress !== undefined) progress.value = data.progress
    }
    if (data.status === 'completed') {
      setTimeout(() => { visible.value = false; emit('done') }, 800)
    }
  }
  ws.onclose = () => { setTimeout(() => { visible.value = false; emit('done') }, 500) }
}

watch(() => props.projectId, (v) => { if (v) connect() })

defineExpose({ connect })
</script>
