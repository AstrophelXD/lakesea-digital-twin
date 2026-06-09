# 顶尖优秀版改造对照清单

> 用于答辩前逐项核对。状态：`[x]` 已完成 · `[ ]` 待完成 · `[~]` 部分完成  
> 最后更新：2026-06-06

---

## 优先级说明

```text
P0  必须完成，直接影响优秀档
P1  拉开「顶尖」与「普通优秀」差距
P2  加分项，时间够再做
P3  代码质量与报告支撑
```

---

## P0：必须完成

### 1. 达梦 DM8 实机跑通

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| 增加 `backend/.env.dm8.example` | [x] | 达梦连接串示例 |
| 增加 `docs/dm8-deployment.md` | [x] | 启动、配置、建表、种子、验证全流程 |
| 修复 DM8 兼容（CLOB/Text、时间、分页、布尔、自增） | [x] | ORM Text 映射；`IS_DELETED` 用 INT；`IDENTITY` 自增；DM8 跳过 `create_all` |
| `init_db.sql` 补充真实外键约束 | [x] | 主从表 + 试验数据 7 组 FK |
| `GET /api/health/db` 健康检查 | [x] | 返回库类型、连接状态、核心表数量 |
| 首页显示当前数据库类型 | [x] | 工作台标签：达梦 DM8 / SQLite |
| **实机验收：删 SQLite 后 DM8 完整跑通** | [ ] | 需在本机达梦环境实测并截图 |

**验收截图（待补）：**

- [ ] 达梦连接界面
- [ ] 表结构（含外键）
- [ ] 表数据与系统页面一致

---

### 2. 用户管理页真实化

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| 新建 `UserManageView.vue` | [x] | 替换 Placeholder |
| 用户列表、角色、启停 | [x] | |
| 新增 / 编辑 / 重置密码 | [x] | |
| `GET/POST/PUT /api/users` | [x] | |
| `POST /api/users/{id}/reset-password` | [x] | |
| `POST /api/users/{id}/disable` | [x] | |
| 仅 ADMIN 可访问 `/users` | [x] | 路由 + 菜单双重控制 |
| 非管理员无权限提示 | [x] | 跳转工作台 + `ElMessage.warning` |

**验收录屏：**

- [ ] 管理员能管理用户
- [ ] 学生/教师/主任看不到用户管理菜单

---

### 3. 首页驾驶舱

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| 完善 `DashboardView.vue` | [x] | |
| 4 个统计卡片 | [x] | 今日预约、运行试验、可用资源、待处理告警 |
| 3 个 ECharts 图表 | [x] | 预约状态、资源状态、7 天告警趋势 |
| 快速演示链路按钮 | [x] | 预约 / 监控 / AI |
| `GET /api/dashboard/summary` | [x] | |
| `GET /api/dashboard/reservation-status` | [x] | |
| `GET /api/dashboard/resource-status` | [x] | |
| `GET /api/dashboard/alarm-trend` | [x] | |
| 图表数据来自后端 | [x] | 非前端硬编码 |

---

## P1：拉开差距

### 4. 预约主从表重点展示页

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| 详情页：上方主表、下方资源明细 | [x] | `ReservationView.vue` 详情弹窗 |
| 资源明细增删改数量备注 | [x] | 编辑表单内 |
| 提交前资源冲突检测 | [x] | `POST /api/reservations/{id}/check-conflicts` |
| 审批流时间线（草稿→提交→教师→主任→任务） | [x] | `el-steps` + 审批日志 |
| `EXP_APPROVAL_LOG` 前端展示 | [x] | 时间线组件 |
| 驳回必填原因 | [x] | 前后端均有校验 |
| 审批通过跳转试验任务 | [x] | `experimentTaskId` 链接 |

**答辩话术准备：**

- [ ] 能讲清 `EXP_RESERVATION` 主表 + `EXP_RESERVATION_RESOURCE` 从表
- [ ] 能现场演示资源冲突校验

---

### 5. 数字孪生监控页

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| 四区布局（任务列表 / 场景 / 数据面板 / 底部曲线） | [x] | `MonitorView.vue` |
| 模型船实时移动 + 轨迹线 | [x] | `TwinScene.vue` + WebSocket |
| 告警时模型船高亮 | [x] | `highlight` 属性 |
| 告警弹窗 + 写入 `ALARM_RECORD` | [x] | |
| WebSocket 状态（已连接/重连中/已断开） | [x] | |
| 模拟试验开始 / 暂停 / 结束 | [x] | |
| 演示告警按钮（低电量/越界/数据突变） | [x] | `POST /api/monitor/{id}/demo-alarm` |
| 刷新稳定 ≥1 秒一次 | [x] | `_tick_interval = 1.0` |

---

### 6. 试验归档回放

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| 历史试验列表（左侧表格） | [x] | `ArchiveView.vue` |
| 时间轴 slider + 播放/暂停/重置 | [x] | 统一时间轴控制 |
| 模型船轨迹回放 | [x] | `TrackReplay` controlled 模式 |
| 当前时刻传感器数据 | [x] | 速度/电量/阻力/横摇 |
| 曲线图同步定位 | [x] | ECharts `showTip` + 横摇曲线 |
| 告警点标记 + 跳转 | [x] | `alarmMarkers` + Slider marks |
| 导出传感器 CSV | [x] | `GET .../export/sensor-csv` |
| 导出轨迹 JSON | [x] | `GET .../export/track-json` |
| 导出 AI 报告 Markdown/HTML | [x] | `GET .../export/ai-report?fmt=` |
| 文件上传（报告/原始数据/视频占位） | [x] | 类型 REPORT / RAW_DATA / VIDEO |
| 与 AI 分析页联动 | [x] | 入口按钮 + aiReport 摘要 + 导出 |
| 归档回放文档 | [x] | `docs/archive-replay.md` |

---

### 7. AI 分析报告

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| 报告生成工作流（选任务→汇总→选类型→生成→展示→入库） | [x] | `AiReportView.vue` |
| 4 种分析类型 | [x] | OVERVIEW / ANOMALY / RISK / SUGGESTION |
| 报告固定分段结构 | [x] | Mock 模板已分段 |
| DeepSeek Key 仅后端读取 | [x] | |
| 页面显示 Mock / DeepSeek API 模式 | [x] | `analysisMode` |
| AI 调用日志（时间/模型/mock/token/失败原因） | [x] | `AI_CALL_LOG` + `GET /api/ai/logs` + 页面日志表 |
| 试验数据摘要预览 API | [x] | `GET /api/ai/reports/summary/{id}` |
| 报告列表 API | [x] | `GET /api/ai/reports/list` |
| 报告保存、查询、重新生成 | [x] | |
| AI 分析文档 | [x] | `docs/ai-report.md` |

---

## P2：加分项

### 8. MQTT 模拟接入

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| `backend/app/services/mqtt_service.py` | [x] | 订阅、解析、入库、WebSocket 广播 |
| `ENABLE_MQTT` 等配置开关 | [x] | `backend/.env.example`、`config.py` |
| MQTT 消息写入 `SENSOR_DATA` | [x] | `MonitorService.persist_frame` 复用 |
| `python -m scripts.mock_mqtt_publisher` | [x] | `backend/scripts/mock_mqtt_publisher.py` |
| `GET /api/monitor/mqtt/info` | [x] | Broker 状态与主题 |
| 监控页数据源标识 | [x] | `MonitorView.vue` MQTT/WebSocket 标签 |
| 文档说明 WebSocket 默认、MQTT 可选 | [x] | `docs/mqtt-integration.md` |

---

### 9. 审计日志

| 任务 | 状态 | 说明 / 文件 |
|------|------|-------------|
| `SYS_OPERATION_LOG` 表 | [x] | `init_db.sql` + ORM `SysOperationLog` |
| 记录登录/预约/审批/资源/告警/AI 等操作 | [x] | 各 Service 埋点 |
| 后端统一日志装饰器或中间件 | [x] | `AuditService` + IP 中间件 + `@audited` |
| `GET /api/audit/logs` | [x] | 仅 ADMIN |
| 前端「操作日志」页（仅管理员） | [x] | `OperationLogView.vue` |
| 审计日志文档 | [x] | `docs/audit-log.md` |

---

### 10. 自动化演示数据与一键重置

| 任务 | 状态 |
|------|------|
| `python -m scripts.reset_demo_db` | [ ] |
| `python -m scripts.seed_demo_flow` | [ ] |
| 一键生成 5 角色 / 10 资源 / 3 预约 / 完整审批链 / 归档试验 / 传感器轨迹告警 AI 数据 | [ ] |
| README「答辩前一键重置」命令 | [ ] |

---

## P3：代码质量与报告支撑

### 11. 测试与验收脚本

| 任务 | 状态 | 说明 |
|------|------|------|
| `pytest` 登录/预约/主从表/冲突/审批/告警/AI 等 | [~] | `backend/tests/` 已有基础用例，需联网 `pip install pytest` |
| `scripts/smoke_test.py` | [x] | 需后端已启动 |
| `npm run build` 通过 | [x] | 已验证 |
| README 写明三条测试命令 | [x] | |

**本地执行：**

```bash
cd backend && pip install pytest && pytest
cd frontend && npm run build
cd backend && python -m scripts.smoke_test   # 先启动 uvicorn
```

---

### 12. 文档与截图清单

| 任务 | 状态 | 文件 |
|------|------|------|
| 完整演示顺序 | [x] | `docs/demo-script.md` |
| 报告截图清单 | [x] | `docs/screenshot-checklist.md` |
| 本对照清单 | [x] | `docs/todo-checklist.md` |
| AI 分析报告说明 | [x] | `docs/ai-report.md` |
| MQTT 模拟接入说明 | [x] | `docs/mqtt-integration.md` |
| 操作审计日志说明 | [x] | `docs/audit-log.md` |

---

## 最终验收：完整演示链路

答辩当天按顺序走通，逐项打勾：

```text
[ ] 1.  管理员登录
[ ] 2.  首页驾驶舱查看系统状态（含数据库类型）
[ ] 3.  学生登录并创建试验预约
[ ] 4.  预约中添加多个资源明细
[ ] 5.  资源冲突检测（可选演示）
[ ] 6.  教师审核
[ ] 7.  主任审批
[ ] 8.  系统生成试验任务
[ ] 9.  试验任务：准备 → 启动
[ ] 10. 进入数字孪生监控页
[ ] 11. 启动模拟数据（模型船运动 + 曲线）
[ ] 12. 触发演示告警
[ ] 13. 完成试验并归档
[ ] 14. 归档页时间轴回放
[ ] 15. 生成 AI 分析报告（含数据摘要、调用日志）
[ ] 16. 达梦库中查看主从表、任务、告警、AI_REPORT、AI_CALL_LOG、SYS_OPERATION_LOG 数据
```

---

## 建议执行顺序（剩余工作）

若时间有限，优先补齐：

1. **达梦实机联调 + 截图**（P0-1 唯一未实机项）
2. **一键演示重置**（P2-10，答辩当天保险）
3. 一键演示重置（P2-10）

---

## 进度统计

| 级别 | 已完成 | 部分完成 | 待完成 |
|------|--------|----------|--------|
| P0 | 17 | 0 | 1（实机验收） |
| P1 | 38 | 0 | 0 |
| P2 | 13 | 0 | 4 |
| P3 | 5 | 1 | 0 |

> 勾选方式：直接在本文档把 `[ ]` 改成 `[x]`，或用 IDE 任务插件跟踪。
