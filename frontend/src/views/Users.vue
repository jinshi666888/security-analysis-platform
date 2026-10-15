<template>
  <div>
    <el-button type="primary" @click="openCreate">新增用户</el-button>
    <el-table :data="users" style="margin-top:16px">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'analyst' ? 'warning' : 'info'">
            {{ row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用户' : '新增用户'">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="editing" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password
                    :placeholder="editing ? '留空不修改' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role">
            <el-option label="管理员" value="admin" />
            <el-option label="分析师" value="analyst" />
            <el-option label="开发者" value="developer" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listUsers, createUser, updateUser, deleteUser } from '@/api'

const users = ref<any[]>([])
const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref<number | null>(null)
const form = reactive({ username: '', password: '', role: 'analyst', is_active: true })

async function load() { users.value = await listUsers() }

function openCreate() {
  editing.value = false
  editId.value = null
  Object.assign(form, { username: '', password: '', role: 'analyst', is_active: true })
  dialogVisible.value = true
}

function openEdit(row: any) {
  editing.value = true
  editId.value = row.id
  Object.assign(form, { username: row.username, password: '', role: row.role, is_active: row.is_active })
  dialogVisible.value = true
}

async function submit() {
  if (editing.value) {
    await updateUser(editId.value!, { password: form.password || undefined, role: form.role, is_active: form.is_active })
  } else {
    await createUser({ username: form.username, password: form.password, role: form.role })
  }
  dialogVisible.value = false
  ElMessage.success('操作成功')
  load()
}

async function onDelete(row: any) {
  await ElMessageBox.confirm(`确认删除用户 ${row.username}?`, '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
