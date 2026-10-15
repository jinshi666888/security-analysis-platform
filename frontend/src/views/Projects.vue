<template>
  <div>
    <el-button v-if="isAdmin" type="primary" @click="openCreate">新增项目</el-button>
    <el-table :data="projects" style="margin-top:16px">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="项目名" />
      <el-table-column prop="source_path" label="源码路径" show-overflow-tooltip />
      <el-table-column prop="last_gate_status" label="门禁状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.last_gate_status === 'passed' ? 'success' : 'danger'">
            {{ row.last_gate_status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_scan_at" label="最后扫描" width="170" />
      <el-table-column label="操作" width="560">
        <template #default="{ row }">
          <el-button v-if="canOperate" size="small" :loading="scanning === row.id" @click="onScan(row)">扫描</el-button>
          <el-button size="small" type="primary" @click="$router.push(`/projects/${row.id}/findings`)">漏洞</el-button>
          <el-button v-if="canOperate" size="small" @click="$router.push(`/projects/${row.id}/review`)">复核</el-button>
          <el-button size="small" type="success" @click="$router.push(`/projects/${row.id}/report`)">报告</el-button>
          <el-button size="small" @click="$router.push(`/projects/${row.id}/benchmark`)">基线</el-button>
          <el-button size="small" @click="$router.push(`/projects/${row.id}/feedback`)">误报</el-button>
          <el-button v-if="isAdmin" size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新增项目">
      <el-form :model="form" label-width="100px">
        <el-form-item label="项目名"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="源码路径"><el-input v-model="form.source_path" placeholder="如 G:\demo\myproject" /></el-form-item>
        <el-form-item label="扫描器">
          <el-select v-model="form.scanners" multiple style="width:100%">
            <el-option v-for="s in scanners" :key="s.name" :label="scannerLabel(s)"
                       :value="s.name" :disabled="s.available === false" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreate">确定</el-button>
      </template>
    </el-dialog>

    <ScanProgress ref="scanProgressRef" :project-id="scanProjectId" @done="onScanDone" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listProjects, createProject, deleteProject, triggerScan, listScanners } from '@/api'
import { useAuthStore } from '@/stores/auth'
import ScanProgress from '@/components/ScanProgress.vue'

const auth = useAuthStore()
const isAdmin = computed(() => auth.role === 'admin')
// 安全分析师可执行扫描与复核写入；开发者只读
const canOperate = computed(() => auth.role === 'admin' || auth.role === 'analyst')

const projects = ref<any[]>([])
const scanners = ref<any[]>([])
const dialogVisible = ref(false)
const scanning = ref<number | null>(null)
const scanProjectId = ref<number | null>(null)
const scanProgressRef = ref<any>(null)
const form = reactive({ name: '', source_path: '', scanners: [] as string[] })

async function load() { projects.value = await listProjects() }

async function loadScanners() {
  try { scanners.value = await listScanners() } catch { scanners.value = [] }
}

function scannerLabel(s: any) {
  const state = s.available === false ? '不可用' : s.available === true ? '可用' : '未知'
  return `${s.name} (${state})`
}

async function openCreate() {
  if (!scanners.value.length) await loadScanners()
  Object.assign(form, { name: '', source_path: '' })
  // 默认勾选可用扫描器；若无法探测则全选
  const ready = scanners.value.filter(s => s.available === true).map(s => s.name)
  form.scanners = ready.length ? ready : scanners.value.map(s => s.name)
  dialogVisible.value = true
}

async function onCreate() {
  if (!form.name.trim()) { ElMessage.warning('请填写项目名'); return }
  await createProject({
    name: form.name,
    source_path: form.source_path,
    scanners: form.scanners.join(','),
  })
  dialogVisible.value = false
  ElMessage.success('创建成功')
  load()
}

async function onScan(row: any) {
  scanProjectId.value = row.id
  scanProgressRef.value?.connect()
  scanning.value = row.id
  try {
    await triggerScan(row.id)
    ElMessage.success('扫描完成')
    load()
  } finally { scanning.value = null }
}

function onScanDone() {
  load()
}

async function onDelete(row: any) {
  await ElMessageBox.confirm(`确认删除项目 ${row.name}?`, '提示', { type: 'warning' })
  await deleteProject(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
