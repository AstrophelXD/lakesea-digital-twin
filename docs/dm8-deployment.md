# 达梦 DM8 部署指南

本文说明如何在达梦 DM8 上完整跑通湖海试验场数字孪生系统，用于课程答辩实机演示。

## 0. 一键脚本（推荐）

项目根目录 **`lakesea.bat`** 汇总了安装、启服、重置、测试等常用操作：

| 命令 | 说明 |
|------|------|
| `lakesea.bat` | 交互菜单 |
| `lakesea.bat setup-dm8` | 首次达梦环境：venv、依赖、dmPython、`.env`、引导建表与灌数 |
| `lakesea.bat defense-dm8` | **答辩推荐**：`reset_demo_db --full` + 启后端/前端 + 开浏览器 |
| `lakesea.bat reset` | 仅重置演示数据（不清服务） |
| `lakesea.bat run` | 仅启动前后端（不重置） |
| `lakesea.bat test` | pytest 16 项（独立 SQLite 测试库，不连达梦） |
| `lakesea.bat smoke` | 端到端冒烟（需先启动后端，**达梦验收推荐**） |

答辩当天典型流程：

```bat
REM 1. 确认达梦服务已启动、init_db.sql 已执行、backend\.env 已配置 DM8 连接串
lakesea.bat defense-dm8

REM 2. 后端起来后可选冒烟
lakesea.bat smoke
```

仍可使用旧脚本：`pre-defense.bat`（SQLite 默认）、`reset-demo.bat`、`run-all.bat`、`setup.bat`，功能已并入 `lakesea.bat`。

---

## 1. 环境准备

| 组件 | 版本建议 |
|------|----------|
| 达梦数据库 | DM8 |
| Python | 3.11+ |
| dmPython 驱动 | 与 DM8 版本匹配 |
| Node.js | 18+ |

### 安装 dmPython

在已安装达梦数据库的机器上，通常可从达梦安装目录获取 dmPython 安装包：

```bash
cd backend
.venv\Scripts\activate
pip install dmPython
```

> 若 pip 无法安装，请从达梦官网/SDK 目录手动安装对应版本。`lakesea.bat setup-dm8` 会自动尝试安装。

---

## 2. 启动达梦服务

### Windows

1. 打开「达梦数据库配置工具」或「服务」管理器。
2. 确认 `DmService` 实例状态为 **运行中**。
3. 默认端口一般为 **5236**。

### Linux

```bash
# 进入达梦安装目录的 bin
./DmServiceDMSERVER start
```

### 验证连接

使用「达梦数据库管理工具」或 `disql` 连接：

```text
主机：localhost
端口：5236
用户：SYSDBA（或自建用户）
```

---

## 3. 创建数据库/模式

在管理工具中执行（可按需修改库名）：

```sql
CREATE SCHEMA LAKESEA;
-- 或使用已有用户/模式，确保对该模式有 DDL/DML 权限
```

---

## 4. 执行建表脚本

1. 在达梦管理工具中连接到目标库/模式。
2. 打开并执行项目脚本：

   ```text
   backend/scripts/init_db.sql
   ```

3. 确认 **15 张核心业务表** 已创建（含外键）：

| 分类 | 表名 |
|------|------|
| 用户权限 | `SYS_USER`、`SYS_ROLE`、`SYS_USER_ROLE` |
| 资源 | `LAB_RESOURCE` |
| 预约主从表 | `EXP_RESERVATION`、`EXP_RESERVATION_RESOURCE` |
| 审批 | `EXP_APPROVAL_LOG` |
| 试验 | `EXPERIMENT_TASK`、`EXPERIMENT_FILE` |
| 监控 | `SENSOR_DATA`、`SHIP_TRACK`、`ALARM_RECORD` |
| AI | `AI_REPORT`、`AI_CALL_LOG` |
| 审计 | `SYS_OPERATION_LOG` |

主从表与外键（管理工具「表结构 → 外键」可核对）：

- `EXP_RESERVATION_RESOURCE.RESERVATION_ID → EXP_RESERVATION.ID`
- `EXP_RESERVATION_RESOURCE.RESOURCE_ID → LAB_RESOURCE.ID`
- `EXPERIMENT_TASK.RESERVATION_ID → EXP_RESERVATION.ID`
- `SENSOR_DATA.EXPERIMENT_ID → EXPERIMENT_TASK.ID`
- 其余见 `init_db.sql` 末尾 `ALTER TABLE` 语句

> 达梦环境**不要**依赖 SQLAlchemy `create_all`；表结构以 `init_db.sql` 为准。`reset_demo_db` 会通过 `schema_migrate` 在 SQLite 下自动补列，达梦侧需保持脚本与库一致。

---

## 5. 配置后端环境变量

```bat
cd backend
copy .env.dm8.example .env
```

编辑 `backend/.env`，至少修改达梦连接串：

```env
DATABASE_URL=dm+dmPython://SYSDBA:YourPassword@localhost:5236/LAKESEA
DEBUG=false
MOCK_AI=true
```

连接串格式：

```text
dm+dmPython://用户名:密码@主机:端口/库名或模式名
```

### 可选配置

| 变量 | 说明 | 答辩建议 |
|------|------|----------|
| `MOCK_AI` | `true` 本地模拟 AI 报告，无需 Key | 默认 `true`，稳定演示 |
| `DEEPSEEK_API_KEY` | 真实 DeepSeek 调用 | 有网有 Key 时设 `MOCK_AI=false` |
| `ENABLE_MQTT` | MQTT 接入开关 | 默认 `false`，用 WebSocket 模拟即可 |
| `CORS_ORIGINS` | 前端地址 | 保持 `http://localhost:5173` |

完整示例见 `backend/.env.dm8.example`。

---

## 6. 安装依赖并写入种子数据

### 方式 A：一键（推荐）

```bat
lakesea.bat setup-dm8
```

按提示在达梦管理工具执行 `init_db.sql`、修改 `DATABASE_URL` 后，脚本会执行 `reset_demo_db --full`。

### 方式 B：手动

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install dmPython
copy .env.dm8.example .env
REM 编辑 .env 后：
python -m scripts.reset_demo_db --full
```

### 种子数据说明

| 命令 | 作用 |
|------|------|
| `python -m scripts.seed_db` | 5 角色用户 + 5 条基础资源 |
| `python -m scripts.seed_demo_flow` | 追加完整演示流程 |
| `python -m scripts.reset_demo_db --full` | 清空业务表 + 基础种子 + 演示流程（**推荐**） |

`--full` 后包含：10 条资源、3 条预约（草稿/待主任/已归档）、`TASK-DEMO-ARCHIVED`（80 点传感器、轨迹、3 条告警、AI 报告与调用日志）。详见 [demo-data.md](./demo-data.md)。

达梦与 SQLite 重置差异：

- **SQLite**：优先删除 `lakesea.db` 重建；文件被占用则清空表
- **达梦**：按依赖顺序 `DELETE` 清空业务表后重新写入；**需先执行 `init_db.sql`**

---

## 7. 启动后端

```bat
lakesea.bat run
```

或手动：

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 验证数据库健康检查

```bash
curl http://127.0.0.1:8000/api/health/db
```

期望返回（`coreTableTotal` 为各表**行数之和**，非表个数）：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "databaseType": "达梦 DM8",
    "connected": true,
    "tableCounts": {
      "SYS_USER": 5,
      "LAB_RESOURCE": 10,
      "EXP_RESERVATION": 3,
      "AI_REPORT": 1,
      "SYS_OPERATION_LOG": 0
    },
    "coreTableTotal": 120
  }
}
```

`tableCounts` 中某表为 `-1` 表示该表不存在，请重新执行 `init_db.sql`。

---

## 8. 启动前端并验证

`lakesea.bat run` / `defense-dm8` 会自动启动前端；手动启动：

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173 ，使用 `admin / 123456` 登录。

首页工作台应显示：**当前数据库：达梦 DM8**。

---

## 9. 测试与验收

### 自动化测试分工

| 方式 | 数据库 | 何时使用 |
|------|--------|----------|
| `lakesea.bat test`（pytest） | 独立 `test_lakesea.db` | 开发回归，不依赖达梦 |
| `lakesea.bat smoke` | 当前 `.env` 指向的库 | **达梦答辩前验收** |

pytest 覆盖：登录鉴权、预约主从表、冲突检测、两级审批、试验状态机、告警处理、AI Mock 报告等 16 项（`backend/tests/`）。

冒烟测试（需后端已启动）：

```bat
lakesea.bat smoke
```

### 答辩验收检查清单

- [ ] 删除或重命名本地 `backend/lakesea.db`，确认 `.env` 仅指向达梦
- [ ] `GET /api/health/db` 返回 `databaseType: 达梦 DM8` 且 `connected: true`
- [ ] 达梦管理工具中可见 15 张业务表及主从表数据
- [ ] `lakesea.bat defense-dm8` 或 `reset_demo_db --full` 输出正常（3 预约 / 归档试验 / AI 报告）
- [ ] 完成预约 → 审批 → 试验 → 告警 → AI 报告全流程后，DM8 表数据与页面一致
- [ ] `lakesea.bat smoke` 通过（可选截图）
- [ ] 截图：达梦连接、表结构（含外键）、表数据、系统页面对比

截图清单见 [screenshot-checklist.md](./screenshot-checklist.md)，演示顺序见 [demo-script.md](./demo-script.md)。

---

## 10. 常见问题

### 连接失败

- 检查达梦服务是否启动、端口是否为 5236
- 检查用户名密码、模式名是否与 `DATABASE_URL` 一致
- 确认 `dmPython` 已正确安装（`pip show dmPython`）
- Windows 防火墙是否放行 5236

### `reset_demo_db` 失败

- 达梦未建表：先执行 `init_db.sql`
- 连接串错误：用管理工具用相同账号测试登录
- 外键冲突：使用项目自带 `reset_demo_db`，不要手动乱删主表

### 表不存在（health 中 count 为 -1）

在达梦管理工具重新执行 `backend/scripts/init_db.sql`，或对比缺失表名单独补建。

### CLOB / 大文本字段

ORM 中 `PURPOSE`、`PLAN_SUMMARY`、`SUMMARY_TEXT` 等使用 `Text` 类型，达梦侧映射为 `CLOB`，无需额外配置。

### 自增主键

`init_db.sql` 使用 `IDENTITY(1,1)` 自增；种子脚本通过 ORM 插入时不指定 ID 即可。

### 预约单号冲突

业务单号生成已含微秒时间戳（`RSV{yyyyMMddHHmmssffffff}`），批量脚本写入时一般不会撞号。

### 分页查询

后端统一使用 `offset/limit` 分页，达梦 DM8 兼容。

### 布尔 / 逻辑删除

`IS_DELETED` 等字段使用 `INT`（0/1），避免 DM8 布尔类型差异。

### pytest 与达梦

pytest 固定使用 `sqlite:///./test_lakesea.db` 与 `MOCK_AI=true`（见 `backend/tests/conftest.py`），**不会连接达梦**。达梦环境请用 `smoke_test` 与页面手工验收。

### 后端占用导致 SQLite 文件未删除

仅影响 SQLite 开发环境；达梦环境按表清空，不受此限制。若本地混用，答辩前请确认 `.env` 中 `DATABASE_URL` 为达梦连接串。

---

## 11. 相关文档

| 文档 | 内容 |
|------|------|
| [demo-data.md](./demo-data.md) | 演示数据清单与重置命令 |
| [demo-script.md](./demo-script.md) | 答辩现场演示顺序 |
| [screenshot-checklist.md](./screenshot-checklist.md) | 截图验收项 |
| [mqtt-integration.md](./mqtt-integration.md) | MQTT 可选接入 |
| [audit-log.md](./audit-log.md) | 操作审计日志 |
| [ai-report.md](./ai-report.md) | AI 报告与 DeepSeek 配置 |
