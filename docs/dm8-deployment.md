# 达梦 DM8 部署指南

本文说明如何在达梦 DM8 上完整跑通湖海试验场数字孪生系统，用于课程答辩实机演示。

## 1. 环境准备

| 组件 | 版本建议 |
|------|----------|
| 达梦数据库 | DM8 |
| Python | 3.11+ |
| dmPython 驱动 | 与 DM8 版本匹配 |
| Node.js | 18+ |

### 安装 dmPython

在已安装达梦数据库的机器上，通常可从达梦安装目录获取 dmPython 安装包，或使用：

```bash
pip install dmPython
```

> 若 pip 无法安装，请从达梦官网/SDK 目录手动安装对应版本。

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

## 3. 创建数据库/模式

在管理工具中执行（可按需修改库名）：

```sql
CREATE SCHEMA LAKESEA;
-- 或使用已有用户/模式，确保对该模式有 DDL/DML 权限
```

## 4. 执行建表脚本

1. 在达梦管理工具中连接到目标库。
2. 打开并执行项目脚本：

   ```text
   backend/scripts/init_db.sql
   ```

3. 确认以下核心表已创建，且外键约束存在：
   - `EXP_RESERVATION` / `EXP_RESERVATION_RESOURCE`（主从表）
   - `EXPERIMENT_TASK`
   - `SENSOR_DATA` / `SHIP_TRACK` / `ALARM_RECORD`
   - `AI_REPORT`

可在管理工具「表结构 → 外键」中查看：
- `EXP_RESERVATION_RESOURCE.RESERVATION_ID → EXP_RESERVATION.ID`
- `EXP_RESERVATION_RESOURCE.RESOURCE_ID → LAB_RESOURCE.ID`
- `EXPERIMENT_TASK.RESERVATION_ID → EXP_RESERVATION.ID`
- `SENSOR_DATA.EXPERIMENT_ID → EXPERIMENT_TASK.ID`
- 等（详见 `init_db.sql` 末尾 ALTER 语句）

## 5. 配置后端环境变量

```bash
cd backend
copy .env.dm8.example .env    # Windows
# cp .env.dm8.example .env    # Linux/macOS
```

编辑 `.env`，设置达梦连接串：

```env
DATABASE_URL=dm+dmPython://SYSDBA:YourPassword@localhost:5236/LAKESEA
DEBUG=false
MOCK_AI=true
```

连接串格式：

```text
dm+dmPython://用户名:密码@主机:端口/库名或模式名
```

## 6. 安装依赖并写入种子数据

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
pip install dmPython            # 若 requirements 中未自动安装
python -m scripts.seed_db
python -m scripts.reset_demo_db --full   # 可选：完整答辩演示数据
```

种子数据将创建 5 个演示账号（密码均为 `123456`）和 5 条资源记录。`--full` 另含 3 条预约、已归档试验、传感器/告警/AI 报告，见 [demo-data.md](./demo-data.md)。

## 7. 启动后端

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证数据库健康检查：

```bash
curl http://127.0.0.1:8000/api/health/db
```

期望返回：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "databaseType": "达梦 DM8",
    "connected": true,
    "tableCounts": { "SYS_USER": 5, ... },
    "coreTableTotal": 20
  }
}
```

## 8. 启动前端并验证

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173 ，使用 `admin / 123456` 登录。

首页工作台应显示：**当前数据库：达梦 DM8**。

## 9. 答辩验收检查清单

- [ ] 删除本地 `lakesea.db`（SQLite）后，系统仍能通过 DM8 正常运行
- [ ] 达梦管理工具中可看到业务表及主从表数据
- [ ] 完成预约 → 审批 → 试验 → 告警 → AI 报告全流程后，DM8 表数据与页面一致
- [ ] 截图：达梦连接、表结构（含外键）、表数据、系统页面对比

## 10. 常见问题

### 连接失败

- 检查达梦服务是否启动、端口是否为 5236
- 检查用户名密码、防火墙
- 确认 `dmPython` 已正确安装

### CLOB / 大文本字段

ORM 中 `PURPOSE`、`PLAN_SUMMARY`、`SUMMARY_TEXT` 等使用 `Text` 类型，达梦侧映射为 `CLOB`，无需额外配置。

### 自增主键

`init_db.sql` 使用 `IDENTITY(1,1)` 自增；种子脚本通过 ORM 插入时不指定 ID 即可。

### 分页查询

后端统一使用 `offset/limit` 分页，达梦 DM8 兼容。

### 布尔 / 逻辑删除

`IS_DELETED` 等字段使用 `INT`（0/1），避免 DM8 布尔类型差异。
