<template>
  <div v-if="finding">
    <el-button @click="$router.back()">返回</el-button>
    <el-button v-if="canRegister" type="success" style="margin-left:8px" @click="openSrc">登记为 SRC 提交</el-button>
    <el-alert v-else-if="(auth.role === 'admin' || auth.role === 'analyst') && finding.status !== 'confirmed'"
              type="info" :closable="false" style="margin-top:8px"
              title="仅 confirmed 状态的漏洞可登记为 SRC 提交" />
    <el-descriptions :column="3" border style="margin-top:16px">
      <el-descriptions-item label="ID">{{ finding.id }}</el-descriptions-item>
      <el-descriptions-item label="严重级"><el-tag :type="sevTag(finding.severity)">{{ finding.severity }}</el-tag></el-descriptions-item>
      <el-descriptions-item label="类型">{{ finding.type }}</el-descriptions-item>
      <el-descriptions-item label="文件" :span="2">{{ finding.file }}</el-descriptions-item>
      <el-descriptions-item label="行号">{{ finding.line }}</el-descriptions-item>
      <el-descriptions-item label="状态">{{ finding.status }}</el-descriptions-item>
      <el-descriptions-item label="来源">{{ finding.source }}</el-descriptions-item>
      <el-descriptions-item label="置信度">{{ finding.confidence }}</el-descriptions-item>
    </el-descriptions>

    <el-card style="margin-top:16px">
      <template #header>证据</template>
      <pre><code>{{ finding.evidence }}</code></pre>
    </el-card>

    <el-card v-if="taint && taint.taint_path" style="margin-top:16px">
      <template #header>污点传播链路</template>
      <TaintGraph :taint-path="taint.taint_path" />
      <div v-for="(hop, idx) in taint.taint_path" :key="idx" class="hop">
        <div class="hop-head">
          <el-tag :type="idx === 0 ? 'danger' : idx === taint.taint_path.length - 1 ? 'warning' : 'info'">
            {{ idx === 0 ? 'SOURCE' : idx === taint.taint_path.length - 1 ? 'SINK' : 'PROPAGATION' }}
          </el-tag>
          <span>{{ hop.file }}:{{ hop.lines }}</span>
        </div>
        <pre class="hop-code">{{ hop.code }}</pre>
        <div v-if="hop.transform" class="hop-transform">变换: {{ hop.transform }}</div>
      </div>
    </el-card>

    <el-card v-if="finding.classification" style="margin-top:16px">
      <template #header>定级信息</template>
      <p>CWE: {{ finding.classification.cwe }} ({{ finding.classification.cwe_name }})</p>
      <p>OWASP: {{ finding.classification.owasp?.id }} {{ finding.classification.owasp?.name }}</p>
      <p>CVSS: {{ finding.classification.cvss?.score }} ({{ finding.classification.cvss?.severity }})</p>
      <p>向量: {{ finding.classification.cvss?.vector }}</p>
      <p>优先级: {{ finding.priority?.level }} — {{ finding.priority?.sla }}</p>
    </el-card>

    <el-card v-if="finding.triage" style="margin-top:16px">
      <template #header>AI 定级</template>
      <p>状态: {{ finding.triage.status }}</p>
      <p>原因: {{ finding.triage.reason }}</p>
      <p v-if="finding.triage.fix">修复: {{ finding.triage.fix.summary }}</p>
    </el-card>

    <el-dialog v-model="srcVisible" title="登记为 SRC 提交" width="520px">
      <el-form :model="srcForm" label-width="100px">
        <el-form-item label="关联任务">
          <el-select v-model="srcForm.task_id" clearable filterable placeholder="可选" style="width:320px">
            <el-option v-for="t in tasks" :key="t.id" :label="`#${t.id} [${t.platform}] ${t.title}`" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="平台"><el-input v-model="srcForm.platform" placeholder="不选任务时手工填写" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="srcForm.note" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="srcVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSrc">登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFinding, listSrcTasks, submissionFromFinding } from '@/api'
import { useAuthStore } from '@/stores/auth'
import TaintGraph from '@/components/TaintGraph.vue'

const route = useRoute()
const auth = useAuthStore()
const finding = ref<any>(null)
const taint = ref<any>(null)
const canRegister = computed(() => finding.value?.status === 'confirmed'
  && (auth.role === 'admin' || auth.role === 'analyst'))

const srcVisible = ref(false)
const tasks = ref<any[]>([])
const srcForm = reactive({ task_id: undefined as number | undefined, platform: '', note: '' })

async function load() {
  const res = await getFinding(Number(route.params.id), String(route.params.fid))
  finding.value = res.finding
  taint.value = res.taint
}

function sevTag(s: string) {
  return { critical: 'danger', high: 'warning', medium: '', low: 'info', info: 'info' }[s] || ''
}

async function openSrc() {
  Object.assign(srcForm, { task_id: undefined, platform: '', note: '' })
  const res = await listSrcTasks({ limit: 200, offset: 0 })
  tasks.value = res.items
  srcVisible.value = true
}

async function submitSrc() {
  const payload: any = {
    project_id: Number(route.params.id),
    finding_id: String(route.params.fid),
    platform: srcForm.platform,
    note: srcForm.note,
  }
  if (srcForm.task_id) payload.task_id = srcForm.task_id
  await submissionFromFinding(payload)
  srcVisible.value = false
  ElMessage.success('已登记为 SRC 提交，可在「SRC 众测 → 提交追踪」跟进')
}

onMounted(load)
</script>

<style scoped>
.hop { margin-bottom: 12px; padding: 12px; background: #f5f7fa; border-radius: 4px; }
.hop-head { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; }
.hop-code { background: #282c34; color: #abb2bf; padding: 8px; border-radius: 4px; font-size: 15px; overflow-x: auto; }
.hop-transform { color: #e6a23c; margin-top: 4px; font-size: 15px; }
</style>
