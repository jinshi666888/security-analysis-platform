import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/login', component: () => import('@/views/Login.vue') },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: () => import('@/views/Dashboard.vue') },
      { path: 'projects', component: () => import('@/views/Projects.vue') },
      { path: 'projects/:id/findings', component: () => import('@/views/Findings.vue') },
      { path: 'projects/:id/findings/:fid', component: () => import('@/views/FindingDetail.vue') },
      { path: 'projects/:id/review', component: () => import('@/views/Review.vue') },
      { path: 'projects/:id/report', component: () => import('@/views/Report.vue') },
      { path: 'projects/:id/benchmark', component: () => import('@/views/Benchmark.vue') },
      { path: 'projects/:id/feedback', component: () => import('@/views/Feedback.vue') },
      { path: 'users', component: () => import('@/views/Users.vue'), meta: { adminOnly: true } },
      { path: 'audit', component: () => import('@/views/Audit.vue'), meta: { adminOnly: true } },
      { path: 'src/tasks', component: () => import('@/views/SrcTasks.vue') },
      { path: 'src/submissions', component: () => import('@/views/SrcSubmissions.vue') },
      { path: 'earnings', component: () => import('@/views/Earnings.vue') },
      { path: 'withdrawals', component: () => import('@/views/Withdrawals.vue') },
      { path: 'notifications', component: () => import('@/views/Notifications.vue') },
      { path: 'knowledge', component: () => import('@/views/Knowledge.vue') },
    ]
  },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.path === '/login') return true
  if (!auth.token) return '/login'
  // 刷新页面后 token 仍在 localStorage，但角色/用户名需回填
  if (!auth.role) await auth.fetchMe()
  if (!auth.token) return '/login'
  if (to.meta.adminOnly && auth.role !== 'admin') return '/dashboard'
  return true
})

export default router
