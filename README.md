# 🌊 校园湖海试验场数字孪生全景监控与数据管理系统

<p align="center">
  <img src="https://img.shields.io/badge/Course-应用软件架构课程设计-0F766E?style=for-the-badge" alt="Course Badge" />
  <img src="https://img.shields.io/badge/Frontend-Vue%203%20%2B%20TypeScript-42B883?style=for-the-badge" alt="Frontend Badge" />
  <img src="https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python%203.11-009688?style=for-the-badge" alt="Backend Badge" />
  <img src="https://img.shields.io/badge/Database-DM8-国产数据库-blue?style=for-the-badge" alt="Database Badge" />
  <img src="https://img.shields.io/badge/Realtime-WebSocket%20%2F%20MQTT-2563EB?style=for-the-badge" alt="Realtime Badge" />
  <img src="https://img.shields.io/badge/AI-DeepSeek-7C3AED?style=for-the-badge" alt="AI Badge" />
</p>

<p align="center">
  面向高校船舶与海洋工程湖海试验场的课程设计项目，聚焦
  <strong>预约审批、资源管理、数字孪生监控、实时数据采集、异常告警、试验归档与 AI 分析</strong>。
</p>

---

## ✨ 项目简介

本项目服务于《应用软件架构课程设计》，目标不是做一个完整工业级平台，而是在课程设计范围内，完成一个：

- 架构清晰的前后端分离系统
- 具备主从表业务亮点的管理平台
- 能展示实时监控与数字孪生效果的可演示项目
- 能体现国产数据库 DM8 与 DeepSeek API 集成能力的综合案例

系统围绕试验全流程展开：

```text
预约草稿 → 提交预约 → 教师审核 → 主任审批 → 生成试验任务
→ 任务准备 → 现场试验 → 实时监控与告警 → 数据归档 → AI 分析报告
```

---

## 🧭 核心亮点

- 🔐 登录与角色权限管理：支持管理员、主任、教师、学生/研究员、维护人员等角色。
- 🧾 主从表业务设计：`EXP_RESERVATION` + `EXP_RESERVATION_RESOURCE`，满足课程设计重点要求。
- 🛠️ 后端分层架构：遵循 `API → Service → Repository → Model/Database`。
- 🛰️ 实时监控：通过 WebSocket 推送模型船位置、姿态、电量、阻力等模拟数据。
- 🚨 异常告警：支持越界、低电量、设备离线、数据突变等告警。
- 🤖 AI 分析：由后端调用 DeepSeek API 生成试验摘要、异常说明和改进建议。
- 🗃️ 国产数据库应用：核心业务数据基于达梦 DM8 设计。

---

## 🏗️ 总体架构

```text
Browser
  ↓
Vue 3 + TypeScript + Element Plus + ECharts + Three.js
  ↓
FastAPI + WebSocket
  ↓
Service / Repository / ORM
  ↓
DM8 + File Storage
  ↓
DeepSeek API / Simulated Data Source / MQTT(optional)
```

课程设计 `v1` 统一采用：

- 固定两级审批：教师审核 + 主任审批
- 资源冲突策略：提交预校验 + 主任审批前终校验
- 任务状态机：`PENDING_PREPARE → READY → RUNNING → COMPLETED → ARCHIVED`
- 重要业务数据：默认逻辑删除并保留审计信息

---

## 🧩 功能模块

| 模块 | 说明 |
| --- | --- |
| 登录与角色权限 | 用户登录、菜单鉴权、接口权限控制 |
| 试验预约与审批 | 草稿、提交、教师审核、主任审批、任务生成 |
| 资源设备管理 | 水池、模型船、传感器、摄像头等资源管理 |
| 数字孪生监控 | 模型船位置、轨迹、状态、场景可视化 |
| 实时数据与告警 | WebSocket 推送、曲线刷新、异常告警 |
| 归档与 AI 分析 | 历史任务、回放、文件、AI 报告 |

---

## 🗂️ 文档导航

当前仓库已优先完成设计文档收敛，后续编码请优先参考以下文件：

- [总体设计文档](./docs/architecture.md)
- [需求与范围说明](./docs/requirements.md)
- [数据库详细设计](./docs/database-design.md)
- [接口详细设计](./docs/api-design.md)
- [Agent 协作约束](./AGENTS.md)

---

## 🧱 推荐目录结构

```text
lakesea-digital-twin/
├── AGENTS.md
├── README.md
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── database-design.md
│   └── api-design.md
├── frontend/
└── backend/
```

> 当前仓库已包含完整的前后端实现，本地开发默认使用 SQLite，生产/答辩可切换达梦 DM8。

---

## 🛠️ 技术栈

### Frontend

- Vue 3
- TypeScript
- Vite
- Element Plus
- ECharts
- Three.js / Cesium

### Backend

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- WebSocket

### Database & Integration

- 达梦 DM8
- DeepSeek API
- MQTT（可选）
- 本地文件存储

---

## 📌 当前状态

![Status](https://img.shields.io/badge/Status-Implementation%20Complete-16A34A?style=flat-square)
![Progress](https://img.shields.io/badge/Progress-Ready%20for%20Demo-2563EB?style=flat-square)

当前版本已完成：

- 设计文档与 API/数据库基线
- 前端 Vue 3 工程与核心业务页面
- 后端 FastAPI 分层架构与主要接口
- 试验预约主从表与两级审批流程
- 资源管理与冲突校验
- WebSocket 模拟数据与数字孪生监控页
- 试验归档、轨迹回放与文件管理
- AI 报告生成（五段结构、数据摘要预览、调用日志；支持 `MOCK_AI` 与 DeepSeek API，见 [docs/ai-report.md](./docs/ai-report.md)）
- MQTT 模拟接入（可选，`ENABLE_MQTT=true` + `mock_mqtt_publisher`，见 [docs/mqtt-integration.md](./docs/mqtt-integration.md)）
- 操作审计日志（`SYS_OPERATION_LOG`，管理员操作日志页，见 [docs/audit-log.md](./docs/audit-log.md)）
- 演示数据一键重置（`reset_demo_db --full`，见 [docs/demo-data.md](./docs/demo-data.md)）

可选后续增强：

- 达梦 DM8 生产环境联调与部署
- 真实 DeepSeek API Key 配置（`backend/.env` 中设置 `MOCK_AI=false`）
- 用户管理页、首页驾驶舱等增强功能

---

## 🚀 计划实现的演示链路

1. 管理员登录查看用户和资源
2. 学生创建预约草稿并添加多个资源明细
3. 学生提交预约
4. 教师审核通过
5. 主任审批通过并生成试验任务
6. 启动任务并打开数字孪生监控页
7. 展示模型船轨迹、实时曲线与告警
8. 完成试验并进入归档页面
9. 生成并展示 AI 分析报告

---

## 📖 开发约束

为保证课程设计目标和后续协作一致性，建议实现阶段遵守以下原则：

- 不要绕过 Service 层，复杂业务不得直接写在 API 层
- 不要删除预约主从表设计
- 不要在前端暴露 DeepSeek API Key
- 不要把系统改造成普通设备管理系统
- 不要过度追求真实硬件接入，课程阶段允许模拟数据

---

## 🗺️ Roadmap

### 设计阶段

- [x] 统一需求范围与总体设计
- [x] 明确审批流、资源占用规则、任务状态机
- [x] 补齐数据库与接口详细设计

### 实现阶段

- [x] 搭建前端 Vue 3 工程骨架
- [x] 搭建后端 FastAPI 分层工程骨架
- [x] 实现登录鉴权与角色菜单
- [x] 实现预约审批主从表业务
- [x] 实现资源管理与冲突校验
- [x] 实现试验任务状态流转
- [x] 实现 WebSocket 模拟数据与监控页面
- [x] 实现告警生成与管理
- [x] 实现归档、轨迹回放与文件上传
- [x] 实现 AI 报告生成（Mock / DeepSeek）

### 顶尖优秀版增强（已完成）

- [x] 用户管理真实页面（`UserManageView.vue`）
- [x] 首页驾驶舱统计与 ECharts 图表
- [x] 达梦 DM8 部署文档与外键约束（见 [docs/dm8-deployment.md](./docs/dm8-deployment.md)）
- [x] 数据库健康检查 `GET /api/health/db`
- [x] 预约冲突检测、审批流程展示、任务跳转
- [x] 数字孪生监控四区布局 + 演示告警按钮
- [x] 试验归档回放（时间轴/告警标记/导出/文件上传）见 [docs/archive-replay.md](./docs/archive-replay.md)
- [x] AI 分析报告工作流（摘要预览/调用日志/五段展示）见 [docs/ai-report.md](./docs/ai-report.md)
- [x] MQTT 模拟接入（WebSocket 默认 / MQTT 可选）见 [docs/mqtt-integration.md](./docs/mqtt-integration.md)
- [x] 操作审计日志（Service 埋点 + 管理员查询页）见 [docs/audit-log.md](./docs/audit-log.md)
- [x] 演示数据一键重置（`reset_demo_db` / `seed_demo_flow`）见 [docs/demo-data.md](./docs/demo-data.md)
- [x] 答辩演示脚本与截图清单

### 可选增强

- [x] MQTT 模拟数据接入（可选，`docs/mqtt-integration.md`）
- [x] 操作审计日志（`SYS_OPERATION_LOG`，见 [docs/audit-log.md](./docs/audit-log.md)）
- [ ] 一键演示数据重置脚本

---

## 🚀 快速启动

### Windows 一键启动（推荐）

**首次安装**（pip 默认走本地代理 `127.0.0.1:7897`，请先开启 Clash 等代理）：

```bat
setup.bat
```

**日常启动**：

```bat
run-all.bat
```

将自动打开两个终端窗口（后端 + 前端）并启动浏览器。

### 后端

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip-install.bat
copy .env.example .env
python -m scripts.seed_db
uvicorn app.main:app --reload
```

`pip-install.bat` 会优先走代理 `127.0.0.1:7897`，失败则自动改用清华镜像。  
`requirements-dev.txt` 仅含 pytest，装不上也不影响运行项目。

### 前端

```bash
cd frontend
npm install
npm run dev
```

详细说明见 [backend/README.md](./backend/README.md) 与 [frontend/README.md](./frontend/README.md)。

### 达梦 DM8 部署

```bash
cd backend
copy .env.dm8.example .env    # 修改 DATABASE_URL
# 在达梦管理工具执行 scripts/init_db.sql
python -m scripts.seed_db
uvicorn app.main:app --reload
```

完整步骤见 [docs/dm8-deployment.md](./docs/dm8-deployment.md)。

### 测试与验收

```bash
# 后端单元测试
cd backend && pytest

# 前端构建
cd frontend && npm run build

# 端到端冒烟（需先启动后端）
cd backend && python -m scripts.smoke_test
```

### 答辩前一键准备（Windows 推荐）

双击项目根目录 **`pre-defense.bat`**：

1. 重置并灌入完整演示数据（`reset_demo_db --full`）
2. 自动启动后端 + 前端并打开浏览器

仅重置数据库、不启动服务时，可运行 `reset-demo.bat`。命令行等价：

```bash
cd backend && python -m scripts.reset_demo_db --full
```

答辩演示顺序见 [docs/demo-script.md](./docs/demo-script.md)，演示数据说明见 [docs/demo-data.md](./docs/demo-data.md)，截图清单见 [docs/screenshot-checklist.md](./docs/screenshot-checklist.md)，改造进度对照见 [docs/todo-checklist.md](./docs/todo-checklist.md)。

### 演示账号（密码均为 `123456`）

| 用户名 | 角色 |
| --- | --- |
| `student01` | 学生 |
| `teacher01` | 教师 |
| `director01` | 主任 |
| `admin` | 管理员 |
| `maintainer01` | 维护人员 |

---

## 📄 License

本项目用于课程设计与学习交流，默认按仓库所有者课程用途管理。如需开源许可，可后续补充 `LICENSE` 文件。

