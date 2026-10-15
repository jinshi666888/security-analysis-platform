import http from './http'

export const loginApi = (username: string, password: string) =>
  http.post('/auth/login', { username, password })

export const meApi = () => http.get('/auth/me')

export const listProjects = () => http.get('/projects')
export const createProject = (data: any) => http.post('/projects', data)
export const deleteProject = (id: number) => http.delete(`/projects/${id}`)
export const getProject = (id: number) => http.get(`/projects/${id}`)

export const triggerScan = (id: number) => http.post(`/scans/${id}`)
export const scanHistory = (id: number) => http.get(`/scans/${id}/history`)
export const listScanners = () => http.get('/scanners')

export const listFindings = (id: number, params: any) =>
  http.get(`/findings/${id}`, { params })
export const getFinding = (pid: number, fid: string) =>
  http.get(`/findings/${pid}/${fid}`)
export const dashboardStats = (id: number) =>
  http.get(`/findings/${id}/dashboard/stats`)
export const getReport = (id: number) =>
  http.get(`/findings/${id}/report/content`)
export const getFeedbackRules = (id: number) =>
  http.get(`/findings/${id}/feedback/rules`)
export const getBenchmark = (id: number) =>
  http.get(`/findings/${id}/benchmark/report`)

export const pendingReview = (id: number) => http.get(`/review/${id}/pending`)
export const applyReview = (id: number, data: any) => http.post(`/review/${id}`, data)

export const listUsers = () => http.get('/users')
export const createUser = (data: any) => http.post('/users', data)
export const updateUser = (id: number, data: any) => http.put(`/users/${id}`, data)
export const deleteUser = (id: number) => http.delete(`/users/${id}`)

export const listAudit = (params: any) => http.get('/audit', { params })

// ---- SRC 众测：任务聚合 ----
export const listSrcTasks = (params: any) => http.get('/src/tasks', { params })
export const srcTaskStats = () => http.get('/src/tasks/stats')
export const createSrcTask = (data: any) => http.post('/src/tasks', data)
export const importSrcTasks = (data: any) => http.post('/src/tasks/import', data)
export const deleteSrcTask = (id: number) => http.delete(`/src/tasks/${id}`)

// ---- SRC 众测：提交追踪 ----
export const listSubmissions = (params: any) => http.get('/src/submissions', { params })
export const submissionStats = () => http.get('/src/submissions/stats')
export const createSubmission = (data: any) => http.post('/src/submissions', data)
export const submissionFromFinding = (data: any) => http.post('/src/submissions/from-finding', data)
export const updateSubmission = (id: number, data: any) => http.put(`/src/submissions/${id}`, data)

// ---- 收益 / 提现 ----
export const listEarnings = (params: any) => http.get('/earnings', { params })
export const earningSummary = (params?: any) => http.get('/earnings/summary', { params })
export const createEarning = (data: any) => http.post('/earnings', data)

export const listWithdrawals = (params: any) => http.get('/withdrawals', { params })
export const createWithdrawal = (data: any) => http.post('/withdrawals', data)
export const reviewWithdrawal = (id: number, data: any) => http.post(`/withdrawals/${id}/review`, data)
export const payWithdrawal = (id: number) => http.post(`/withdrawals/${id}/pay`)

// ---- 站内通知 ----
export const listNotifications = (params: any) => http.get('/notifications', { params })
export const unreadCount = () => http.get('/notifications/unread-count')
export const readNotification = (id: number) => http.post(`/notifications/${id}/read`)
export const readAllNotifications = () => http.post('/notifications/read-all')

// ---- 知识库 / 规范 / 合规 ----
export const kbArticles = (params: any) => http.get('/kb/articles', { params })
export const kbArticle = (id: string) => http.get(`/kb/articles/${id}`)
export const kbGuidelines = () => http.get('/kb/guidelines')
export const kbCompliance = () => http.get('/kb/compliance')
