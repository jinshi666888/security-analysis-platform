# Security Analysis Platform

安全分析可视化平台，基于现有 `security-analysis-runtime` 引擎构建，提供 Web 界面进行漏洞管理、人工复核、安全态势看板等功能。

## 技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite
- **前端**：Vue 3 + TypeScript + Element Plus + ECharts
- **引擎**：复用现有 `security-analysis-runtime`（子进程调用）

## 快速启动

### 1. 安装依赖

双击 `setup.bat`，或手动执行：

```bat
cd backend
pip install -r requirements.txt

cd ..\frontend
npm install
```

### 2. 启动服务

**方式一（推荐）**：双击 `start_all.bat`，自动启动前后端两个窗口。

**方式二**：分别启动
```bat
:: 后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

:: 前端（另一个终端）
cd frontend
npm run dev
```

### 3. 访问

- 前端：http://localhost:5173
- 后端 API 文档：http://127.0.0.1:8000/docs
- 默认账号：`admin / admin123`（另有 analyst/analyst123, developer/dev123）

## 配置

编辑 `backend/app/config.py`：

| 配置项 | 说明 |
|---|---|
| `runtime_path` | 现有 runtime 的 `security-analysis-runtime` 目录路径 |
| `python_exe` | Python 解释器路径 |
| `default_out_root` | 扫描产物输出根目录（建议放 G 盘） |
| `secret_key` | JWT 密钥（生产环境务必修改） |

## 使用流程

1. **登录** → 使用 admin 账号登录
2. **新增项目** → 项目管理 → 填写项目名、源码路径，并从「扫描器」下拉（显示各扫描器可用性）中勾选
3. **执行扫描** → 点击「扫描」按钮，等待扫描完成（WebSocket 实时进度）
4. **查看漏洞** → 点击「漏洞」查看列表，支持严重级/状态/关键字筛选
5. **漏洞详情** → 点击某行查看证据、污点链路图、定级信息
6. **人工复核** → 进入「复核」批量确认漏洞或标记误报
7. **安全态势** → 看板查看严重级分布、CWE Top10、OWASP 分布、扫描器来源
8. **报告** → 在线预览安全报告，支持导出 Markdown

## 功能模块

| 模块 | 说明 |
|---|---|
| 安全态势看板 | 总览卡片 + 4 个图表（严重级饼图/CWE柱图/OWASP雷达/来源柱图） |
| 项目管理 | 新增/删除项目，触发扫描 |
| 漏洞列表 | 多维度筛选、搜索、分页、点击查看详情 |
| 漏洞详情 | 8字段契约 + 证据 + 污点链路图(ECharts Graph) + CWE/OWASP/CVSS |
| 人工复核 | 批量决策（confirmed/false_positive/accepted_risk/needs_review） |
| 质量基线 | precision/recall/FP rate/confirmed rate 指标 |
| 误报规则 | 查看反馈生成的 suppression 规则 |
| 报告中心 | Markdown 在线渲染 + 导出 |
| 扫描器探测 | 读取 runtime `list-scanners`，可视化各扫描器可用性，供新增项目时选择 |
| 用户管理 | 管理员专属：增删改用户、角色分配 |
| 操作审计日志 | 管理员专属：记录登录/建项/扫描/复核/用户变更，支持按操作类型筛选分页 |

## 生产部署（Nginx）

1. 构建前端：`cd frontend && npm run build`
2. 启动后端（后台运行）：`uvicorn app.main:app --host 127.0.0.1 --port 8000`
3. 配置 Nginx（见 `nginx/nginx.conf`），将 `root` 指向 `frontend/dist`
4. 访问 Nginx 监听端口（默认 80）

## 角色权限

| 角色 | 权限 |
|---|---|
| admin | 全部功能 + 用户管理 + 审计日志 + 项目增删 |
| analyst | 扫描、漏洞查看、复核、报告、基线、误报规则（不可建项/删项） |
| developer | 漏洞查看、报告、基线、误报规则（只读） |

> 权限在服务端强制校验（`app/api/deps.py: require_role`），前端菜单与按钮同步隐藏。
> 读接口对所有已登录用户开放；写接口按上表限制。

## API 接口一览

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/auth/login` | 匿名 | 登录，返回 JWT |
| GET | `/api/auth/me` | 登录 | 当前用户信息 |
| GET | `/api/projects` | 登录 | 项目列表 |
| POST | `/api/projects` | admin | 新增项目（校验路径存在、项目名唯一） |
| DELETE | `/api/projects/{id}` | admin | 删除项目 |
| POST | `/api/scans/{id}` | admin/analyst | 触发扫描并等待完成 |
| GET | `/api/scans/{id}/history` | 登录 | 扫描历史 |
| GET | `/api/scanners` | 登录 | 扫描器可用性探测 |
| GET | `/api/findings/{id}` | 登录 | 漏洞列表（筛选/分页） |
| GET | `/api/findings/{id}/{fid}` | 登录 | 漏洞详情（契约+证据+污点链路） |
| GET | `/api/findings/{id}/dashboard/stats` | 登录 | 看板统计 |
| GET | `/api/findings/{id}/report/content` | 登录 | Markdown 报告 |
| GET | `/api/findings/{id}/benchmark/report` | 登录 | 质量基线 |
| GET | `/api/findings/{id}/feedback/rules` | 登录 | 误报 suppression 规则 |
| GET | `/api/review/{id}/pending` | 登录 | 待复核清单 |
| POST | `/api/review/{id}` | admin/analyst | 批量提交复核结论 |
| GET/POST/PUT/DELETE | `/api/users[/{id}]` | admin | 用户管理 |
| GET | `/api/audit` | admin | 操作审计日志（筛选/分页） |
| WS | `/ws/scan/{id}` | 登录 | 扫描进度推送 |

## 目录结构

```
platform/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI 入口
│   │   ├── config.py            配置
│   │   ├── database.py          SQLAlchemy
│   │   ├── models/              ORM 模型
│   │   ├── schemas/             Pydantic 模型
│   │   ├── api/                 API 路由（projects/scans/findings/review/users/scanners/audit）
│   │   ├── services/            业务逻辑（scanner/findings_reader/audit）
│   │   └── websocket/           WebSocket 扫描进度
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/               页面组件（含 Audit.vue 审计日志）
│   │   ├── components/          通用组件（TaintGraph/ScanProgress）
│   │   ├── stores/              Pinia
│   │   ├── router/              路由
│   │   └── api/                 Axios 封装
│   └── package.json
├── nginx/nginx.conf             Nginx 生产配置
├── setup.bat                    一键安装
├── start_all.bat                一键启动
├── start_backend.bat
└── start_frontend.bat
```
