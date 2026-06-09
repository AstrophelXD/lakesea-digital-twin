# 自动化演示数据与一键重置

答辩前可将数据库恢复为「开箱即用」状态：含完整审批链、已归档试验、传感器轨迹、告警与 AI 报告。

## 脚本说明

| 命令 | 作用 |
|------|------|
| `python -m scripts.seed_db` | 基础种子：5 角色用户 + 5 条资源 |
| `python -m scripts.seed_demo_flow` | 在基础种子上追加完整演示流程数据 |
| `python -m scripts.reset_demo_db` | 清空并重建（SQLite 删库重建） |
| `python -m scripts.reset_demo_db --full` | 重置 + 基础种子 + 演示流程（**推荐**） |

Windows 答辩前一键（项目根目录，**推荐**）：

```bat
pre-defense.bat
```

等价于 `reset_demo_db --full` + 启动后端/前端/浏览器。

仅重置数据库：

```bat
reset-demo.bat
```

## 演示数据清单

### 账号（密码均为 `123456`）

| 用户名 | 角色 |
|--------|------|
| admin | 系统管理员 |
| director01 | 试验场主任 |
| teacher01 | 指导教师 |
| student01 | 学生/研究员 |
| maintainer01 | 设备维护人员 |

### 资源设备（10 条）

基础 5 条（`seed_db`）+ 扩展 5 条（`seed_demo_flow`）：水池×2、模型船×2、传感器、摄像头×2、拖车、供电单元等。

### 预约（3 条）

| 单号 | 状态 | 用途 |
|------|------|------|
| `RSV-DEMO-ARCHIVED` | 已归档 | 归档回放、AI 分析、导出 |
| `RSV-DEMO-PENDING` | 待主任审批 | 主任审批现场演示 |
| `RSV-DEMO-DRAFT` | 草稿 | 学生新建/提交演示 |

### 已归档试验 `TASK-DEMO-ARCHIVED`

- 完整两级审批日志（`EXP_APPROVAL_LOG`）
- 80 点 `SENSOR_DATA` + `SHIP_TRACK`
- 3 条 `ALARM_RECORD`（低电量、近边界、阻力突变）
- 1 份 `AI_REPORT` + `AI_CALL_LOG`

## 使用场景

**答辩当天早上：**

```bash
cd backend
python -m scripts.reset_demo_db --full
# 重启 uvicorn
```

**仅补演示数据（保留现有库）：**

```bash
python -m scripts.seed_demo_flow
```

若已存在 `RSV-DEMO-ARCHIVED` 会跳过，需先 `reset_demo_db`。

## SQLite vs 达梦

- **SQLite**：优先删除 `lakesea.db` 重建；若后端占用文件则清空表并自动补齐缺列（`schema_migrate`）
- **达梦 DM8**：按表依赖顺序 `DELETE` 清空后重新 `seed_db`；需先执行 `init_db.sql` 建表

若后端正在运行导致无法删除 `lakesea.db`，脚本会自动改为清空表数据后重新写入。建议完成后重启后端。

## 相关文件

| 文件 | 说明 |
|------|------|
| `backend/scripts/reset_demo_db.py` | 重置入口 |
| `backend/scripts/seed_demo_flow.py` | 演示流程种子 |
| `backend/scripts/demo_seed_common.py` | 轨迹/预约生成工具 |
| `backend/scripts/seed_db.py` | 基础用户与资源 |
| `pre-defense.bat` | 答辩前一键（重置 + 启服） |
| `reset-demo.bat` | 仅重置数据库 |
