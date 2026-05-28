# AGENTS.md

## Project Overview

本项目为《应用软件架构课程设计》项目，题目为：

**校园湖海试验场数字孪生全景监控与数据管理系统**

系统面向高校船舶与海洋工程湖海试验场，围绕“预约—准备—执行—分析—归档”流程，建设集试验预约审批、资源设备管理、数字孪生全景监控、实时数据采集、异常告警、试验数据归档和 AI 智能分析于一体的综合管理平台。

本项目优先满足课程设计评分要求，重点体现：

* 4—6 个可展示功能点；
* 至少 1 个主从表业务功能；
* 清晰的前后端分离架构；
* 后端分层架构；
* 达梦 DM8 国产数据库应用；
* DeepSeek API 接口调用；
* WebSocket / MQTT 实时数据接口；
* 数字孪生监控展示。

---

## Core Business Scope

### Main Business Process

系统主流程为：

```text
学生/研究员提交试验预约
        ↓
指导教师审核试验方案
        ↓
试验场主任审批资源占用
        ↓
系统生成试验任务
        ↓
设备与模型船准备
        ↓
现场试验执行
        ↓
数字孪生监控 + 数据采集
        ↓
异常告警与现场处置
        ↓
试验数据归档
        ↓
DeepSeek 生成试验摘要与分析建议
```

### Key Features

优先实现以下 6 个功能：

1. 登录与角色权限管理
2. 试验预约与审批
3. 试验资源与设备管理
4. 数字孪生全景监控
5. 实时数据采集与告警
6. 试验数据归档与 AI 分析

---

## Tech Stack

### Frontend

* Vue 3
* TypeScript
* Vite
* Element Plus
* ECharts
* Cesium or Three.js
* WebSocket client

### Backend

* Python 3.11
* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn
* WebSocket
* MQTT optional / simulated data source
* DeepSeek API

### Database

* 达梦 DM8
* SQLAlchemy ORM
* 达梦 Python 驱动 or ODBC

### Tools

* VS Code / Cursor
* Postman
* 达梦数据库管理工具
* npm
* pip / Poetry
* Docker optional

---

## Recommended Repository Structure

```text
project-root/
│
├── AGENTS.md
├── README.md
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── database-design.md
│   └── api-design.md
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── router/
│       ├── api/
│       ├── views/
│       ├── components/
│       ├── stores/
│       └── utils/
│
└── backend/
    ├── requirements.txt
    ├── pyproject.toml
    ├── app/
    │   ├── main.py
    │   ├── core/
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   └── security.py
    │   │
    │   ├── api/
    │   │   ├── auth_api.py
    │   │   ├── user_api.py
    │   │   ├── reservation_api.py
    │   │   ├── resource_api.py
    │   │   ├── experiment_api.py
    │   │   ├── monitor_api.py
    │   │   ├── alarm_api.py
    │   │   └── ai_api.py
    │   │
    │   ├── services/
    │   │   ├── auth_service.py
    │   │   ├── reservation_service.py
    │   │   ├── resource_service.py
    │   │   ├── experiment_service.py
    │   │   ├── monitor_service.py
    │   │   ├── alarm_service.py
    │   │   └── ai_service.py
    │   │
    │   ├── repositories/
    │   │   ├── user_repository.py
    │   │   ├── reservation_repository.py
    │   │   ├── resource_repository.py
    │   │   ├── experiment_repository.py
    │   │   ├── sensor_repository.py
    │   │   └── alarm_repository.py
    │   │
    │   ├── models/
    │   │   ├── user.py
    │   │   ├── reservation.py
    │   │   ├── resource.py
    │   │   ├── experiment.py
    │   │   ├── sensor_data.py
    │   │   ├── alarm.py
    │   │   └── ai_report.py
    │   │
    │   └── schemas/
    │       ├── user_schema.py
    │       ├── reservation_schema.py
    │       ├── resource_schema.py
    │       ├── experiment_schema.py
    │       └── ai_schema.py
    │
    └── scripts/
        ├── init_db.sql
        └── seed_data.sql
```

---

## Architecture Rules

### Backend Layering

后端必须保持分层清晰，不要把所有逻辑写在 API 路由中。

推荐职责划分：

| Layer            | Folder          | Responsibility    |
| ---------------- | --------------- | ----------------- |
| API Layer        | `api/`          | 接收请求、参数校验、返回响应    |
| Service Layer    | `services/`     | 业务逻辑、流程控制、事务处理    |
| Repository Layer | `repositories/` | 数据库增删改查           |
| Model Layer      | `models/`       | SQLAlchemy 数据库模型  |
| Schema Layer     | `schemas/`      | Pydantic 请求和响应模型  |
| Core Layer       | `core/`         | 数据库连接、配置、安全、Token |

### Important Rule

禁止在 API 层直接写复杂业务逻辑或 SQL。

正确方式：

```text
API → Service → Repository → Model / Database
```

---

## Main Domain Models

### User and Role

* `SYS_USER`
* `SYS_ROLE`
* `SYS_USER_ROLE`

### Reservation Main-Detail Tables

课程设计重点主从表：

* 主表：`EXP_RESERVATION`
* 从表：`EXP_RESERVATION_RESOURCE`

关系：

```text
EXP_RESERVATION 1 —— N EXP_RESERVATION_RESOURCE
```

业务含义：

一次试验预约可以占用多个资源，例如拖曳水池、模型船、IMU 传感器、摄像头、拖车设备等。

### Experiment Data

* `EXPERIMENT_TASK`
* `SENSOR_DATA`
* `SHIP_TRACK`
* `ALARM_RECORD`
* `VIDEO_RECORD`
* `EXPERIMENT_FILE`
* `AI_REPORT`

---

## Database Naming Rules

### Table Names

数据库表名统一使用大写英文和下划线：

```text
EXP_RESERVATION
EXP_RESERVATION_RESOURCE
LAB_RESOURCE
SENSOR_DATA
ALARM_RECORD
AI_REPORT
```

### Column Names

字段名统一使用大写英文和下划线：

```text
ID
EXP_NAME
EXP_TYPE
APPLICANT_ID
START_TIME
END_TIME
STATUS
CREATE_TIME
UPDATE_TIME
```

### Primary Key

所有业务表推荐使用：

```text
ID BIGINT PRIMARY KEY
```

### Time Fields

通用时间字段：

```text
CREATE_TIME
UPDATE_TIME
```

### Logical Delete

如需删除重要业务数据，优先使用逻辑删除字段：

```text
IS_DELETED
```

---

## API Design Rules

### RESTful Style

接口路径以 `/api` 开头。

Examples:

```text
POST   /api/auth/login
GET    /api/reservations
POST   /api/reservations
GET    /api/reservations/{id}
PUT    /api/reservations/{id}
POST   /api/reservations/{id}/submit
POST   /api/reservations/{id}/teacher-review
POST   /api/reservations/{id}/director-approve
GET    /api/resources
POST   /api/resources
GET    /api/experiments/{id}/replay
POST   /api/ai/reports/generate
```

### Unified Response Format

所有普通 HTTP 接口应返回统一格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### Error Response Format

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

### WebSocket

实时监控接口建议：

```text
/ws/monitor/{experiment_id}
```

用途：

* 推送模型船位置
* 推送速度、姿态、电量
* 推送传感器数据
* 推送告警信息

---

## Frontend Rules

### Page Organization

推荐页面：

```text
views/
├── LoginView.vue
├── DashboardView.vue
├── ReservationView.vue
├── ResourceView.vue
├── MonitorView.vue
├── AlarmView.vue
├── ArchiveView.vue
├── AiReportView.vue
└── UserManageView.vue
```

### Component Organization

推荐组件：

```text
components/
├── ReservationForm.vue
├── ResourceDetailTable.vue
├── ApprovalDialog.vue
├── TwinScene.vue
├── SensorChart.vue
├── AlarmList.vue
├── TrackReplay.vue
└── AiReportPanel.vue
```

### Frontend Coding Rules

* 页面组件负责展示和交互。
* API 请求统一放在 `src/api/`。
* 不要在 Vue 页面中硬编码大量模拟数据。
* 可将模拟数据放在 mock 文件或后端模拟接口中。
* 数字孪生页面优先保证展示效果和实时刷新，不追求复杂真实三维建模。

---

## Backend Coding Rules

### FastAPI Router Rules

每个业务模块单独一个 router 文件。

Example:

```python
router = APIRouter(prefix="/api/reservations", tags=["试验预约"])
```

API 层只做：

* 接收参数
* 调用 Service
* 返回统一响应

### Service Rules

Service 层负责核心业务逻辑。

例如 `ReservationService` 应包含：

* 创建预约
* 校验资源时间冲突
* 保存预约主表和资源明细
* 提交预约
* 教师审核
* 主任审批
* 生成试验任务

### Repository Rules

Repository 层负责数据库操作。

例如 `ReservationRepository` 应包含：

* 根据 ID 查询预约
* 分页查询预约
* 新增预约主表
* 新增预约资源明细
* 更新预约状态
* 查询资源时间冲突

---

## Important Business Rules

### Reservation Rules

1. 预约开始时间必须早于结束时间。
2. 同一资源在同一时间段内不能被重复预约。
3. 学生提交预约后进入待教师审核状态。
4. 教师审核通过后进入待主任审批状态。
5. 本期课程设计统一采用固定两级审批，不区分是否跳过主任审批。
6. 主任审批通过后生成正式试验任务。
7. 审批驳回必须填写原因。
8. 已完成、已归档或已取消的预约不能再次审批。
9. 创建预约时，主表和从表必须在同一事务中保存。
10. 提交预约时执行资源冲突预校验，主任审批通过前执行终校验。

### Resource Rules

1. 资源状态包括：可用、已预约、使用中、维护中、故障、停用。
2. 故障、停用、维护中的资源不能被预约。
3. 预约草稿不锁定资源。
4. 预约提交后，对未来时间段形成预约占用。
5. 试验执行中，相关资源状态变为使用中。
6. 设备维护人员可以更新资源状态。

### Alarm Rules

告警类型包括：

* 模型船接近边界
* 模型船越界
* 电池电量过低
* 传感器数据突变
* 设备离线
* 速度超过阈值
* 数据长时间未更新

---

## AI Integration Rules

### DeepSeek API Usage

DeepSeek API 只允许后端调用，前端不得直接保存或暴露 API Key。

AI 分析功能应由 `AiService` 负责。

推荐流程：

```text
前端点击“生成 AI 分析”
        ↓
AiReport API
        ↓
AiService 查询试验数据
        ↓
组装 Prompt
        ↓
调用 DeepSeek API
        ↓
保存 AI_REPORT
        ↓
返回前端展示
```

### AI Report Should Include

* 试验概况
* 关键数据摘要
* 异常现象说明
* 可能原因分析
* 风险提示
* 后续改进建议

### Prompt Input Data

生成 AI 报告时，优先提供结构化摘要，不要传入过多原始数据。

Example:

```text
试验名称：模型船阻力测试
试验类型：阻力试验
最大速度：2.4 m/s
最大横摇角：18°
最大阻力：35.6 N
告警数量：3
主要告警：模型船接近边界 2 次，IMU 数据突变 1 次
```

---

## Real-Time Monitoring Rules

### Simulated Data

课程设计阶段允许使用模拟数据。

模拟数据应包含：

* 模型船 X / Y 坐标
* 速度
* 航向角
* 横摇角
* 纵摇角
* 电量
* 阻力
* 时间戳

### WebSocket Message Example

```json
{
  "experimentId": 1001,
  "shipCode": "M-001",
  "timestamp": "2026-05-28 10:30:00",
  "position": {
    "x": 12.5,
    "y": 6.8
  },
  "speed": 2.1,
  "heading": 35.0,
  "roll": 4.2,
  "pitch": 1.8,
  "battery": 76,
  "alarm": null
}
```

---

## Testing Guidelines

### Backend Tests

重点测试：

* 登录接口
* 创建预约
* 预约资源明细保存
* 资源时间冲突校验
* 审批流程
* 告警生成
* AI 报告生成

### Frontend Tests

重点检查：

* 登录后菜单是否按角色显示
* 预约表单是否能提交
* 资源明细是否能增删
* 审批状态是否正确变化
* 数字孪生页面是否能接收实时数据
* AI 报告是否能展示

### Manual Demo Flow

课程展示推荐流程：

1. 管理员登录，查看用户和资源。
2. 学生登录，创建预约草稿并添加多个资源明细。
3. 学生提交试验预约。
4. 教师登录，审核预约。
5. 主任登录，审批预约。
6. 系统生成试验任务。
7. 将任务流转为准备完成并启动试验。
8. 打开数字孪生监控页面。
9. 启动模拟数据，展示模型船运动和曲线变化。
10. 触发低电量或越界告警。
11. 完成试验并打开归档页面。
12. 调用 DeepSeek API 生成试验分析报告。

---

## Development Commands

### Frontend

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务：

```bash
npm run dev
```

构建：

```bash
npm run build
```

### Backend

进入后端目录：

```bash
cd backend
```

创建虚拟环境：

```bash
python -m venv .venv
```

激活虚拟环境：

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --reload
```

### Database

数据库使用达梦 DM8。

初始化脚本建议放在：

```text
backend/scripts/init_db.sql
backend/scripts/seed_data.sql
```

---

## Security Notes

* 不要将数据库密码、DeepSeek API Key 提交到 Git。
* 使用 `.env` 保存敏感配置。
* 前端不得直接调用 DeepSeek API。
* 前端不得保存敏感密钥。
* 删除重要业务数据时优先使用逻辑删除。
* 关键审批操作应记录操作人和操作时间。

---

## What Agents Should Avoid

AI 编程助手在修改本项目时应避免：

1. 不要改变项目主题。
2. 不要把系统改成普通设备管理系统。
3. 不要移除试验预约主从表设计。
4. 不要忽略达梦 DM8 数据库要求。
5. 不要在前端硬编码 DeepSeek API Key。
6. 不要把所有后端逻辑写在一个 `main.py` 中。
7. 不要绕过 Service 层直接在 API 层写复杂业务。
8. 不要使用与课程设计无关的过重技术方案。
9. 不要过度追求真实硬件接入，课程阶段允许模拟数据。
10. 不要删除数字孪生、实时监控、AI 分析等核心亮点。

---

## Priority Implementation Plan

### Phase 1: Basic Framework

* 搭建 Vue 3 前端项目
* 搭建 FastAPI 后端项目
* 连接达梦 DM8 数据库
* 实现统一响应格式
* 实现基础登录

### Phase 2: Core Business

* 实现用户角色
* 实现试验预约主表
* 实现预约资源明细从表
* 实现预约审批流程
* 实现资源设备管理

### Phase 3: Monitoring

* 实现模拟数据生成
* 实现 WebSocket 推送
* 实现数字孪生监控页面
* 实现传感器曲线展示
* 实现告警生成

### Phase 4: Archive and AI

* 实现试验数据归档
* 实现轨迹查询和回放
* 实现 AI 分析报告生成
* 保存 AI 报告到数据库

### Phase 5: Course Report Support

* 准备功能截图
* 准备数据库表截图
* 准备接口截图
* 准备核心代码截图
* 准备达梦数据库使用截图

---

## Final Goal

本项目的最终目标不是实现完整真实的工业级试验场平台，而是在课程设计范围内完成一个结构清晰、功能完整、重点突出的应用软件架构案例。

最终系统应能清楚展示：

* 前后端分离架构
* 后端分层架构
* 主从表业务功能
* 达梦数据库使用
* 实时数据接口
* AI 接口调用
* 数字孪生监控效果
* 试验预约到归档的完整业务闭环
