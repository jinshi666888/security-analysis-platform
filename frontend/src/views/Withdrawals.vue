<template>
  <div>
    <el-row :gutter="12" class="cards">
      <el-col :span="8"><el-card><div class="num ok">¥{{ summary.withdrawable || 0 }}</div><div class="lbl">可提现余额</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="num warn">¥{{ summary.reserved || 0 }}</div><div class="lbl">提现处理中</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="num">¥{{ summary.withdrawn || 0 }}</div><div class="lbl">累计已提现（收益口径）</div></el-card></el-col>
    </el-row>

    <el-card class="filter">
      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width:140px" @change="reload">
            <el-option label="待审核" value="pending" />
            <el-option label="已批准" value="approved" />
            <el-option label="已打款" value="paid" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="auth.role === 'admin'" label="范围">
          <el-checkbox v-model="allUsers" @change="reload">查看全站申请</el-checkbox>
        </el-form-item>
        <el-button type="primary" @click="reload">刷新</el-button>
        <el-button type="success" @click="openApply">申请提现</el-button>
      </el-form>
    </el-card>

    <el-table :data="items" style="margin-top:16px" height="440">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="created_at" label="申请时间" width="180" />
      <el-table-column v-if="allUsers" prop="username" label="申请人" width="120" />
      <el-table-column label="金额" width="120">
        <template #default="{ row }">¥{{ row.amount }}</template>
      </el-table-column>
      <el-table-column label="收款方式" width="140">
        <template #default="{ row }">{{ methodText(row.method) }} {{ row.account }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }"><el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="审核/打款" min-width="200">
        <template #default="{ row }">
          <span v-if="row.review_note">审核备注：{{ row.review_note }}</span>
          <span v-if="row.paid_at"> · 打款：{{ row.paid_at }}</span>
        </template>
      </el-table-column>
      <el-table-column v-if="auth.role === 'admin'" label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button size="small" type="success" @click="review(row, 'approve')">批准</el-button>
            <el-button size="small" type="danger" @click="review(row, 'reject')">驳回</el-button>
          </template>
          <el-button v-else-if="row.status === 'approved'" size="small" type="primary" @click="pay(row)">打款</el-button>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
                   @current-change="load" layout="total, prev, pager, next" />

    <el-dialog v-model="applyVisible" title="申请提现" width="480px">
      <el-alert type="info" :closable="false" class="tip"
                title="站内记账流程：申请 → 审核 → 打款，不涉及真实资金划转。" />
      <el-form :model="form" label-width="100px" style="margin-top:8px">
        <el-form-item label="可提现"><span class="amt">¥{{ summary.withdrawable || 0 }}</span></el-form-item>
        <el-form-item label="提现金额"><el-input-number v-model="form.amount" :min="0" :max="summary.withdrawable || 0" :precision="2" /></el-form-item>
        <el-form-item label="收款方式">
          <el-select v-model="form.method">
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信" value="wechat" />
            <el-option label="银行卡" value="bank" />
          </el-select>
        </el-form-item>
        <el-form-item label="收款账号"><el-input v-model="form.account" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { listWithdrawals, createWithdrawal, reviewWithdrawal, payWithdrawal, earningSummary } from '@/api'

const auth = useAuthStore()
const items = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const summary = reactive<any>({})
const filters = reactive({ status: '' })
const allUsers = ref(false)
const applyVisible = ref(false)
const form = reactive({ amount: 0, method: 'alipay', account: '' })

const methodMap: Record<string, string> = { alipay: '支付宝', wechat: '微信', bank: '银行卡' }
const statusMap: Record<string, string> = { pending: '待审核', approved: '已批准', paid: '已打款', rejected: '已驳回' }
function methodText(m: string) { return methodMap[m] || m }
function statusTag(s: string) { return { pending: 'warning', approved: '', paid: 'success', rejected: 'danger' }[s] || '' }
function statusText(s: string) { return statusMap[s] || s }

async function load() {
  const res = await listWithdrawals({ ...filters, all_users: allUsers.value, limit: pageSize, offset: (page.value - 1) * pageSize })
  items.value = res.items
  total.value = res.total
  Object.assign(summary, await earningSummary({ all_users: allUsers.value }))
}
function reload() { page.value = 1; load() }

function openApply() {
  Object.assign(form, { amount: 0, method: 'alipay', account: '' })
  applyVisible.value = true
}
async function submit() {
  if (form.amount <= 0) { ElMessage.warning('请输入提现金额'); return }
  await createWithdrawal({ ...form })
  applyVisible.value = false
  ElMessage.success('提现申请已提交')
  reload()
}

async function review(row: any, decision: string) {
  const label = decision === 'approve' ? '批准' : '驳回'
  const { value } = await ElMessageBox.prompt(`确认${label}提现申请 #${row.id}（¥${row.amount}）？`, '审核', {
    inputPlaceholder: '审核备注（可选）', inputValue: '',
  })
  await reviewWithdrawal(row.id, { decision, note: value || '' })
  ElMessage.success(`已${label}`)
  reload()
}
async function pay(row: any) {
  await ElMessageBox.confirm(`确认已向该申请打款 ¥${row.amount}？`, '打款确认', { type: 'warning' })
  await payWithdrawal(row.id)
  ElMessage.success('已标记打款')
  reload()
}

onMounted(load)
</script>

<style scoped>
.cards { margin-bottom: 12px; }
.cards .num { font-size: 28px; font-weight: bold; }
.cards .num.ok { color: #67c23a; }
.cards .num.warn { color: #e6a23c; }
.cards .lbl { color: #888; font-size: 14px; }
.filter { margin-bottom: 8px; }
.amt { color: #67c23a; font-weight: bold; }
.tip { margin-bottom: 8px; }
</style>
