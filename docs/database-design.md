# 数据库详细设计（课程设计 v1）

## 1. 设计目标

本文档用于补齐后续实现所需的核心表字段、状态枚举和关键关系，避免 Coding Agent 在建模阶段自行猜测。

设计重点：

1. 保留课程设计要求中的主从表。
2. 支撑固定两级审批流程。
3. 支撑资源冲突校验和任务状态流转。
4. 支撑归档与 AI 报告。

---

## 2. 核心表清单

| 表名 | 说明 |
| --- | --- |
| `SYS_USER` | 用户表 |
| `SYS_ROLE` | 角色表 |
| `SYS_USER_ROLE` | 用户角色关系表 |
| `LAB_RESOURCE` | 资源设备表 |
| `EXP_RESERVATION` | 预约主表 |
| `EXP_RESERVATION_RESOURCE` | 预约资源明细表 |
| `EXP_APPROVAL_LOG` | 审批日志表 |
| `EXPERIMENT_TASK` | 试验任务表 |
| `SENSOR_DATA` | 传感器数据表 |
| `SHIP_TRACK` | 轨迹表 |
| `ALARM_RECORD` | 告警记录表 |
| `EXPERIMENT_FILE` | 试验文件表 |
| `AI_REPORT` | AI 分析报告表 |

---

## 3. 状态枚举建议

### 3.1 预约状态 `EXP_RESERVATION.STATUS`

| 值 | 含义 |
| --- | --- |
| `DRAFT` | 草稿 |
| `PENDING_TEACHER` | 待教师审核 |
| `PENDING_DIRECTOR` | 待主任审批 |
| `APPROVED` | 已审批通过 |
| `REJECTED` | 已驳回 |
| `CANCELLED` | 已取消 |
| `COMPLETED` | 已完成 |
| `ARCHIVED` | 已归档 |

### 3.2 审批结果 `EXP_APPROVAL_LOG.RESULT`

| 值 | 含义 |
| --- | --- |
| `APPROVED` | 通过 |
| `REJECTED` | 驳回 |

### 3.3 审批类型 `EXP_APPROVAL_LOG.STEP_TYPE`

| 值 | 含义 |
| --- | --- |
| `TEACHER_REVIEW` | 教师审核 |
| `DIRECTOR_APPROVAL` | 主任审批 |

### 3.4 资源状态 `LAB_RESOURCE.STATUS`

| 值 | 含义 |
| --- | --- |
| `AVAILABLE` | 可用 |
| `RESERVED` | 已预约 |
| `IN_USE` | 使用中 |
| `MAINTENANCE` | 维护中 |
| `FAULT` | 故障 |
| `DISABLED` | 停用 |

### 3.5 任务状态 `EXPERIMENT_TASK.STATUS`

| 值 | 含义 |
| --- | --- |
| `PENDING_PREPARE` | 待准备 |
| `READY` | 已准备 |
| `RUNNING` | 执行中 |
| `COMPLETED` | 已完成 |
| `ARCHIVED` | 已归档 |
| `CANCELLED` | 已取消 |

### 3.6 告警状态 `ALARM_RECORD.HANDLE_STATUS`

| 值 | 含义 |
| --- | --- |
| `PENDING` | 待处理 |
| `PROCESSING` | 处理中 |
| `RESOLVED` | 已处理 |
| `IGNORED` | 已忽略 |

---

## 4. 主要表字段设计

## 4.1 用户与角色

### 4.1.1 `SYS_USER`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `USERNAME` | VARCHAR(50) | 登录名 |
| `PASSWORD_HASH` | VARCHAR(200) | 密码摘要 |
| `REAL_NAME` | VARCHAR(100) | 姓名 |
| `PHONE` | VARCHAR(30) | 手机号 |
| `EMAIL` | VARCHAR(100) | 邮箱 |
| `STATUS` | VARCHAR(20) | 账户状态 |
| `CREATE_TIME` | TIMESTAMP | 创建时间 |
| `UPDATE_TIME` | TIMESTAMP | 更新时间 |
| `IS_DELETED` | INT | 逻辑删除标记 |

### 4.1.2 `SYS_ROLE`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `ROLE_CODE` | VARCHAR(50) | 角色编码 |
| `ROLE_NAME` | VARCHAR(100) | 角色名称 |
| `CREATE_TIME` | TIMESTAMP | 创建时间 |
| `UPDATE_TIME` | TIMESTAMP | 更新时间 |

### 4.1.3 `SYS_USER_ROLE`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `USER_ID` | BIGINT | 用户 ID |
| `ROLE_ID` | BIGINT | 角色 ID |

## 4.2 资源设备表

### 4.2.1 `LAB_RESOURCE`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `RESOURCE_CODE` | VARCHAR(50) | 资源编码 |
| `RESOURCE_NAME` | VARCHAR(100) | 资源名称 |
| `RESOURCE_TYPE` | VARCHAR(50) | 资源类型 |
| `STATUS` | VARCHAR(20) | 资源状态 |
| `LOCATION` | VARCHAR(200) | 所在位置 |
| `MANAGER_ID` | BIGINT | 维护负责人 |
| `DESCRIPTION` | VARCHAR(500) | 描述 |
| `CREATE_TIME` | TIMESTAMP | 创建时间 |
| `UPDATE_TIME` | TIMESTAMP | 更新时间 |
| `IS_DELETED` | INT | 逻辑删除标记 |

## 4.3 预约主从表

### 4.3.1 `EXP_RESERVATION`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `RESERVATION_NO` | VARCHAR(50) | 预约单号 |
| `EXP_NAME` | VARCHAR(100) | 试验名称 |
| `EXP_TYPE` | VARCHAR(50) | 试验类型 |
| `APPLICANT_ID` | BIGINT | 申请人 ID |
| `TEACHER_ID` | BIGINT | 指导教师 ID |
| `START_TIME` | TIMESTAMP | 计划开始时间 |
| `END_TIME` | TIMESTAMP | 计划结束时间 |
| `STATUS` | VARCHAR(30) | 预约状态 |
| `PURPOSE` | CLOB | 试验目的 |
| `PLAN_SUMMARY` | CLOB | 试验方案摘要 |
| `SUBMIT_TIME` | TIMESTAMP | 提交时间 |
| `TEACHER_REVIEW_BY` | BIGINT | 教师审核人 |
| `TEACHER_REVIEW_TIME` | TIMESTAMP | 教师审核时间 |
| `TEACHER_REVIEW_COMMENT` | VARCHAR(500) | 教师审核意见 |
| `DIRECTOR_APPROVED_BY` | BIGINT | 主任审批人 |
| `DIRECTOR_APPROVED_TIME` | TIMESTAMP | 主任审批时间 |
| `DIRECTOR_APPROVAL_COMMENT` | VARCHAR(500) | 主任审批意见 |
| `REJECT_REASON` | VARCHAR(500) | 最近一次驳回原因 |
| `CREATE_TIME` | TIMESTAMP | 创建时间 |
| `UPDATE_TIME` | TIMESTAMP | 更新时间 |
| `IS_DELETED` | INT | 逻辑删除标记 |

说明：

1. `STATUS` 表示预约主状态，不再拆分两个独立状态字段。
2. 教师和主任各自的审核信息直接落在主表，便于列表查询和页面展示。
3. 更完整的审批历史写入 `EXP_APPROVAL_LOG`。

### 4.3.2 `EXP_RESERVATION_RESOURCE`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `RESERVATION_ID` | BIGINT | 预约单 ID |
| `RESOURCE_ID` | BIGINT | 资源 ID |
| `RESOURCE_TYPE` | VARCHAR(50) | 资源类型 |
| `QUANTITY` | INT | 数量 |
| `START_TIME` | TIMESTAMP | 占用开始时间 |
| `END_TIME` | TIMESTAMP | 占用结束时间 |
| `REMARK` | VARCHAR(500) | 备注 |

说明：

1. 默认与主表时间一致，但保留独立时间字段，方便后续扩展分时占用。
2. 课程设计阶段前端可先按“资源明细时间跟随主表时间”实现。

### 4.3.3 `EXP_APPROVAL_LOG`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `RESERVATION_ID` | BIGINT | 预约单 ID |
| `STEP_TYPE` | VARCHAR(30) | 审批步骤 |
| `APPROVER_ID` | BIGINT | 审批人 |
| `RESULT` | VARCHAR(20) | 审批结果 |
| `COMMENT` | VARCHAR(500) | 审批意见 |
| `ACTION_TIME` | TIMESTAMP | 操作时间 |

## 4.4 试验任务与过程数据

### 4.4.1 `EXPERIMENT_TASK`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `TASK_NO` | VARCHAR(50) | 任务单号 |
| `RESERVATION_ID` | BIGINT | 对应预约 ID |
| `EXP_NAME` | VARCHAR(100) | 试验名称 |
| `STATUS` | VARCHAR(30) | 任务状态 |
| `ACTUAL_START_TIME` | TIMESTAMP | 实际开始时间 |
| `ACTUAL_END_TIME` | TIMESTAMP | 实际结束时间 |
| `OPERATOR_ID` | BIGINT | 现场执行负责人 |
| `ARCHIVE_TIME` | TIMESTAMP | 归档时间 |
| `CREATE_TIME` | TIMESTAMP | 创建时间 |
| `UPDATE_TIME` | TIMESTAMP | 更新时间 |
| `IS_DELETED` | INT | 逻辑删除标记 |

### 4.4.2 `SENSOR_DATA`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `EXPERIMENT_ID` | BIGINT | 试验任务 ID |
| `TIMESTAMP` | TIMESTAMP | 数据时间 |
| `POSITION_X` | DECIMAL(10,2) | X 坐标 |
| `POSITION_Y` | DECIMAL(10,2) | Y 坐标 |
| `SPEED` | DECIMAL(10,2) | 速度 |
| `HEADING` | DECIMAL(10,2) | 航向角 |
| `ROLL` | DECIMAL(10,2) | 横摇角 |
| `PITCH` | DECIMAL(10,2) | 纵摇角 |
| `BATTERY` | DECIMAL(10,2) | 电量 |
| `RESISTANCE` | DECIMAL(10,2) | 阻力 |

### 4.4.3 `SHIP_TRACK`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `EXPERIMENT_ID` | BIGINT | 试验任务 ID |
| `TIMESTAMP` | TIMESTAMP | 轨迹时间 |
| `POSITION_X` | DECIMAL(10,2) | X 坐标 |
| `POSITION_Y` | DECIMAL(10,2) | Y 坐标 |
| `HEADING` | DECIMAL(10,2) | 航向角 |

### 4.4.4 `ALARM_RECORD`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `EXPERIMENT_ID` | BIGINT | 试验任务 ID |
| `ALARM_TYPE` | VARCHAR(50) | 告警类型 |
| `ALARM_LEVEL` | VARCHAR(20) | 告警等级 |
| `ALARM_MESSAGE` | VARCHAR(500) | 告警内容 |
| `HANDLE_STATUS` | VARCHAR(20) | 处理状态 |
| `HANDLER_ID` | BIGINT | 处理人 |
| `HANDLE_TIME` | TIMESTAMP | 处理时间 |
| `HANDLE_COMMENT` | VARCHAR(500) | 处理说明 |
| `CREATE_TIME` | TIMESTAMP | 产生时间 |

### 4.4.5 `EXPERIMENT_FILE`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `EXPERIMENT_ID` | BIGINT | 试验任务 ID |
| `FILE_NAME` | VARCHAR(200) | 文件名 |
| `FILE_TYPE` | VARCHAR(50) | 文件类型 |
| `FILE_PATH` | VARCHAR(500) | 文件路径 |
| `UPLOAD_BY` | BIGINT | 上传人 |
| `UPLOAD_TIME` | TIMESTAMP | 上传时间 |
| `IS_DELETED` | INT | 逻辑删除标记 |

### 4.4.6 `AI_REPORT`

| 字段名 | 类型 | 说明 |
| --- | --- | --- |
| `ID` | BIGINT | 主键 |
| `EXPERIMENT_ID` | BIGINT | 试验任务 ID |
| `REPORT_TITLE` | VARCHAR(200) | 报告标题 |
| `SUMMARY_TEXT` | CLOB | 试验概况与摘要 |
| `ANALYSIS_TEXT` | CLOB | 异常分析与建议 |
| `MODEL_NAME` | VARCHAR(100) | 调用模型名 |
| `GENERATED_BY` | BIGINT | 生成人 |
| `GENERATED_TIME` | TIMESTAMP | 生成时间 |
| `IS_DELETED` | INT | 逻辑删除标记 |

---

## 5. 关键关系说明

1. `EXP_RESERVATION` 与 `EXP_RESERVATION_RESOURCE` 为一对多主从关系，是课程设计重点。
2. `EXP_RESERVATION` 与 `EXPERIMENT_TASK` 为一对一关系。
3. `EXP_RESERVATION` 与 `EXP_APPROVAL_LOG` 为一对多关系，用于保留审批留痕。
4. `EXPERIMENT_TASK` 与 `SENSOR_DATA`、`SHIP_TRACK`、`ALARM_RECORD`、`EXPERIMENT_FILE`、`AI_REPORT` 为一对多关系。

---

## 6. 数据库实现建议

1. 所有主键可由应用层生成雪花 ID、时间戳 ID 或数据库序列，课程设计阶段保持统一即可。
2. 对以下字段建立索引：
   `EXP_RESERVATION.STATUS`、
   `EXP_RESERVATION.APPLICANT_ID`、
   `EXP_RESERVATION.START_TIME`、
   `EXP_RESERVATION.END_TIME`、
   `EXP_RESERVATION_RESOURCE.RESOURCE_ID`、
   `EXPERIMENT_TASK.RESERVATION_ID`、
   `SENSOR_DATA.EXPERIMENT_ID`、
   `ALARM_RECORD.EXPERIMENT_ID`。
3. 资源冲突查询重点依赖 `RESOURCE_ID + START_TIME + END_TIME`。
4. 课程设计阶段允许视频记录先不单独建表，统一并入 `EXPERIMENT_FILE`。

---

## 7. 最小落地建议

如果时间有限，数据库实现优先顺序建议为：

1. `SYS_USER`、`SYS_ROLE`、`SYS_USER_ROLE`
2. `LAB_RESOURCE`
3. `EXP_RESERVATION`
4. `EXP_RESERVATION_RESOURCE`
5. `EXP_APPROVAL_LOG`
6. `EXPERIMENT_TASK`
7. `SENSOR_DATA`
8. `SHIP_TRACK`
9. `ALARM_RECORD`
10. `EXPERIMENT_FILE`
11. `AI_REPORT`
