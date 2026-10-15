<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">Security Analysis</div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item index="/dashboard"><el-icon><DataLine /></el-icon>安全态势</el-menu-item>
        <el-menu-item index="/projects"><el-icon><Folder /></el-icon>项目管理</el-menu-item>
        <el-sub-menu index="src">
          <template #title><el-icon><Search /></el-icon>SRC 众测</template>
          <el-menu-item index="/src/tasks">任务聚合</el-menu-item>
          <el-menu-item index="/src/submissions">提交追踪</el-menu-item>
          <el-menu-item index="/earnings">收益管理</el-menu-item>
          <el-menu-item index="/withdrawals">提现管理</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/knowledge"><el-icon><Reading /></el-icon>知识库与合规</el-menu-item>
        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>通知中心
          <el-badge v-if="unread > 0" :value="unread" class="badge" />
        </el-menu-item>
        <el-menu-item v-if="auth.role === 'admin'" index="/users"><el-icon><User /></el-icon>用户管理</el-menu-item>
        <el-menu-item v-if="auth.role === 'admin'" index="/audit"><el-icon><Document /></el-icon>审计日志</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>{{ auth.username }} ({{ auth.role }})</span>
        <el-button type="danger" size="small" @click="logout">退出</el-button>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { unreadCount } from '@/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const activeMenu = computed(() => route.path)
const unread = ref(0)

function logout() { auth.logout(); router.push('/login') }

onMounted(async () => {
  try { unread.value = (await unreadCount()).unread } catch { unread.value = 0 }
})
</script>

<style scoped>
.layout { height: 100vh; }
.aside { background: #001529; color: #fff; }
.logo { height: 60px; line-height: 60px; text-align: center; font-weight: bold; font-size: 18px; }
.menu { background: #001529; border-right: none; }
.menu :deep(.el-menu-item) { color: #fff; }
.menu :deep(.el-sub-menu__title) { color: #fff; }
.badge { margin-left: 8px; }
.header { display: flex; justify-content: space-between; align-items: center; background: #fff; border-bottom: 1px solid #eee; }
</style>
