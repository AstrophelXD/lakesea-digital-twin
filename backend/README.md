# 后端（FastAPI）

校园湖海试验场数字孪生全景监控与数据管理系统 — 后端服务，基于 Python 3.11 + FastAPI + SQLAlchemy，支持 SQLite（本地开发）与达梦 DM8（答辩部署）。

## 项目目录结构

```text
backend/
├── README.md                    # 本文件
├── requirements.txt             # 生产依赖
├── requirements-dev.txt         # 开发与测试依赖（pytest 等）
├── pip-install.bat              # Windows 一键安装依赖（含代理示例）
├── .env.example                 # 环境变量模板（SQLite 本地开发）
├── .env.dm8.example             # 达梦 DM8 环境变量模板
│
├── app/                         # 应用主包
│   ├── main.py                  # FastAPI 入口，注册路由与生命周期
│   │
│   ├── api/                     # API 层：接收请求、参数校验、返回统一响应
│   │   ├── auth_api.py          # 登录 / 登出 / Token 刷新
│   │   ├── user_api.py          # 用户与角色管理
│   │   ├── reservation_api.py   # 试验预约与两级审批
│   │   ├── resource_api.py      # 试验资源与设备管理
│   │   ├── experiment_api.py    # 试验任务执行与状态流转
│   │   ├── monitor_api.py       # 监控数据查询（传感器、轨迹等）
│   │   ├── alarm_api.py         # 告警记录查询与处置
│   │   ├── dashboard_api.py     # 首页仪表盘统计
│   │   ├── file_api.py          # 试验文件上传与下载
│   │   ├── video_api.py         # 试验视频记录
│   │   ├── ai_api.py            # AI 分析报告生成（DeepSeek）
│   │   ├── audit_api.py         # 操作审计日志
│   │   ├── device_api.py        # 设备指令下发
│   │   ├── cv_api.py            # 计算机视觉跟踪接口
│   │   ├── health_api.py        # 健康检查
│   │   └── ws_monitor.py        # WebSocket 实时监控推送
│   │
│   ├── services/                # 业务逻辑层：流程控制、事务、跨模块协调
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── reservation_service.py
│   │   ├── resource_service.py
│   │   ├── resource_occupancy_service.py  # 资源占用与冲突校验
│   │   ├── experiment_service.py
│   │   ├── monitor_service.py
│   │   ├── alarm_service.py
│   │   ├── dashboard_service.py
│   │   ├── file_service.py
│   │   ├── video_service.py
│   │   ├── ai_service.py
│   │   ├── audit_service.py
│   │   ├── device_command_service.py
│   │   ├── cv_tracking_service.py
│   │   ├── archive_export_service.py      # 试验数据归档导出
│   │   ├── mqtt_service.py                # MQTT 消息订阅（可选）
│   │   └── system_health_service.py
│   │
│   ├── repositories/            # 数据访问层：数据库 CRUD
│   │   ├── user_repository.py
│   │   ├── reservation_repository.py
│   │   ├── resource_repository.py
│   │   ├── experiment_repository.py
│   │   ├── sensor_repository.py
│   │   ├── alarm_repository.py
│   │   ├── file_repository.py
│   │   ├── video_repository.py
│   │   ├── ai_repository.py
│   │   ├── ai_log_repository.py
│   │   ├── audit_repository.py
│   │   └── device_repository.py
│   │
│   ├── models/                  # SQLAlchemy ORM 模型（对应数据库表）
│   │   ├── user.py              # SYS_USER / SYS_ROLE / SYS_USER_ROLE
│   │   ├── reservation.py       # EXP_RESERVATION / EXP_RESERVATION_RESOURCE（主从表）
│   │   ├── resource.py          # LAB_RESOURCE
│   │   ├── experiment.py        # EXPERIMENT_TASK / SENSOR_DATA / SHIP_TRACK 等
│   │   ├── monitor.py           # 监控相关实体
│   │   ├── archive.py           # 归档相关实体
│   │   ├── audit.py             # 审计日志
│   │   ├── device_command.py    # 设备指令
│   │   ├── video_record.py      # 视频记录
│   │   └── constants.py         # 枚举与状态常量
│   │
│   ├── schemas/                 # Pydantic 请求 / 响应模型
│   │   ├── common.py            # 分页、通用字段
│   │   ├── auth_schema.py
│   │   ├── user_schema.py
│   │   ├── reservation_schema.py
│   │   ├── resource_schema.py
│   │   ├── experiment_schema.py
│   │   ├── monitor_schema.py
│   │   ├── alarm_schema.py
│   │   ├── dashboard_schema.py
│   │   ├── archive_schema.py
│   │   ├── ai_schema.py
│   │   ├── audit_schema.py
│   │   ├── device_schema.py
│   │   ├── video_schema.py
│   │   └── cv_schema.py
│   │
│   ├── core/                    # 基础设施：配置、数据库、安全、依赖注入
│   │   ├── config.py            # 环境变量与 Settings
│   │   ├── database.py          # SQLAlchemy 引擎与会话
│   │   ├── security.py          # JWT / 密码哈希
│   │   ├── deps.py              # FastAPI 依赖（当前用户、权限等）
│   │   ├── response.py          # 统一响应封装
│   │   ├── audit_context.py     # 审计上下文（操作人追踪）
│   │   ├── db_info.py           # 数据库连接信息探测
│   │   └── ws_manager.py        # WebSocket 连接管理
│   │
│   └── utils/                   # 工具函数
│       └── ai_report_utils.py   # AI 报告 Prompt 组装等
│
├── scripts/                     # 运维与演示脚本（python -m scripts.xxx 运行）
│   ├── init_db.sql              # 达梦 DM8 建表脚本
│   ├── seed_data.sql            # 达梦初始数据 SQL
│   ├── drop_db.sql              # 达梦删表脚本
│   ├── migrate_max_quantity.sql # 增量迁移示例
│   ├── seed_db.py               # ORM 建表 + 种子数据（SQLite / 通用）
│   ├── reset_demo_db.py         # 答辩前一键重置演示库
│   ├── seed_demo_flow.py        # 完整演示流程数据
│   ├── demo_seed_common.py      # 演示数据公共逻辑
│   ├── schema_migrate.py        # 结构迁移工具
│   ├── generate_demo_video.py   # 生成演示视频
│   ├── mock_mqtt_publisher.py   # 模拟 MQTT 传感器数据
│   ├── mock_device_agent.py     # 模拟设备代理
│   └── smoke_test.py            # 接口冒烟测试
│
├── tests/                       # pytest 测试
│   ├── conftest.py              # 测试 fixtures
│   ├── helpers.py               # 测试辅助函数
│   ├── test_auth.py
│   ├── test_api.py
│   ├── test_reservation.py
│   ├── test_experiment_alarm_ai.py
│   └── test_resource_occupancy.py
│
├── assets/                      # 静态资源（随仓库分发）
│   └── videos/
│       └── demo_pool.mp4        # 演示用拖曳水池视频
│
├── uploads/                     # 运行时上传目录（用户文件、视频副本，不提交 Git）
└── lakesea.db                   # 本地 SQLite 数据库（运行时生成，不提交 Git）
```

### 分层调用关系

```text
API (api/) → Service (services/) → Repository (repositories/) → Model (models/) → Database
                ↑
           Schema (schemas/)  — 请求校验与响应序列化
                ↑
           Core (core/)       — 配置、连接、鉴权、统一响应
```

## 快速启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip-install.bat
:: 或: pip install -r requirements.txt --proxy http://127.0.0.1:7897
:: 测试（可选）: pip install -r requirements-dev.txt --proxy http://127.0.0.1:7897
copy .env.example .env
python -m scripts.seed_db
uvicorn app.main:app --reload
```

### 答辩前一键重置（含完整演示数据）

```bash
python -m scripts.reset_demo_db --full
```

答辩前推荐项目根目录 `pre-defense.bat`（含启服）；仅重置用 `reset-demo.bat`。详见 [docs/demo-data.md](../docs/demo-data.md)。

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

## 演示账号

| 用户名 | 角色 | 密码 |
| --- | --- | --- |
| admin | ADMIN | 123456 |
| director01 | DIRECTOR | 123456 |
| teacher01 | TEACHER | 123456 |
| student01 | STUDENT | 123456 |
| maintainer01 | MAINTAINER | 123456 |

## 数据库

- **本地开发**：默认 SQLite（`lakesea.db`），ORM 自动建表。
- **达梦 DM8**：在 `.env` 中配置 `DATABASE_URL`，并在达梦客户端执行 `scripts/init_db.sql`，再运行 `python -m scripts.seed_db`。
