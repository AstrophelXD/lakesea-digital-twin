# 操作审计日志

系统通过 `SYS_OPERATION_LOG` 表记录关键业务操作，供管理员追溯登录、审批、资源变更等行为。

## 记录范围

| 模块 | 操作 | 触发场景 |
|------|------|----------|
| AUTH | LOGIN / LOGOUT | 登录成功/失败、退出 |
| USER | CREATE / UPDATE / RESET_PASSWORD / DISABLE / ENABLE | 用户管理 |
| RESOURCE | CREATE / UPDATE / DELETE | 资源设备增删改、状态变更 |
| RESERVATION | CREATE / UPDATE / SUBMIT / APPROVE / REJECT / CANCEL | 预约全生命周期 |
| EXPERIMENT | READY / START / FINISH / ARCHIVE | 试验任务状态流转 |
| MONITOR | START / FINISH | 监控启停 |
| ALARM | HANDLE | 告警处理 |
| AI | GENERATE | AI 报告生成 |

每条记录包含：用户、模块、操作、目标对象、详情、IP、成功/失败、时间。

## 实现方式

1. **Service 层埋点**：各业务 Service 在事务成功后调用 `AuditService.log_user()`
2. **IP 中间件**：`main.py` 中 HTTP 中间件写入 `request_ip` 上下文
3. **API 装饰器**（可选）：`audit_service.audited()` 供 API 层快速接入

## API

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/audit/logs` | ADMIN | 分页查询，支持 module/action/keyword/success |
| GET | `/api/audit/meta` | ADMIN | 模块与操作类型字典 |

## 前端

- 菜单：**操作日志**（仅 ADMIN 可见）
- 页面：`OperationLogView.vue` — 筛选 + 表格 + 分页

## 数据库

表名：`SYS_OPERATION_LOG`（见 `backend/scripts/init_db.sql`）

本地 SQLite 由 ORM `create_all` 自动建表；旧库可删除 `lakesea.db` 后重启重建。

## 答辩演示

1. 用 `admin` 登录，完成预约审批或启动试验
2. 打开 **操作日志** 页
3. 按模块筛选「试验预约」或「认证」
4. 展示记录与达梦库 `SYS_OPERATION_LOG` 表数据一致（可选）

## 相关文件

| 层级 | 路径 |
|------|------|
| 模型 | `backend/app/models/audit.py` |
| 服务 | `backend/app/services/audit_service.py` |
| API | `backend/app/api/audit_api.py` |
| 页面 | `frontend/src/views/OperationLogView.vue` |
