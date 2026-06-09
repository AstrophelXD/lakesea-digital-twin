# 接口详细设计（课程设计 v1）

## 1. 设计原则

1. 所有普通 HTTP 接口路径以 `/api` 开头。
2. 统一响应结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

3. 错误响应结构：

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

4. 需要认证的接口使用 Token。
5. WebSocket 独立使用 `/ws/monitor/{experiment_id}`。

---

## 2. 接口分组总览

| 分组 | 路径前缀 | 说明 |
| --- | --- | --- |
| 认证 | `/api/auth` | 登录、退出、当前用户 |
| 用户 | `/api/users` | 用户管理 |
| 资源 | `/api/resources` | 资源设备管理 |
| 预约 | `/api/reservations` | 草稿、提交、审批、取消 |
| 任务 | `/api/experiments` | 任务准备、启动、完成、归档 |
| 告警 | `/api/alarms` | 告警查询与处理 |
| 文件 | `/api/files` | 文件上传下载 |
| AI | `/api/ai/reports` | AI 报告生成与查询 |
| WebSocket | `/ws/monitor/{experiment_id}` | 实时监控推送 |

---

## 3. 认证接口

### 3.1 登录

`POST /api/auth/login`

请求示例：

```json
{
  "username": "student01",
  "password": "123456"
}
```

响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "jwt-token",
    "user": {
      "id": 1,
      "username": "student01",
      "realName": "张三",
      "roles": ["STUDENT"]
    }
  }
}
```

### 3.2 当前用户信息

`GET /api/auth/profile`

### 3.3 退出登录

`POST /api/auth/logout`

---

## 4. 预约与审批接口

## 4.1 查询预约列表

`GET /api/reservations`

建议查询参数：

| 参数 | 说明 |
| --- | --- |
| `status` | 预约状态 |
| `applicantId` | 申请人 ID |
| `teacherId` | 教师 ID |
| `keyword` | 试验名称关键字 |
| `page` | 页码 |
| `pageSize` | 每页条数 |

## 4.2 查询预约详情

`GET /api/reservations/{id}`

返回内容建议包含：

1. 预约主表信息。
2. 预约资源明细列表。
3. 审批日志列表。

## 4.3 创建预约草稿

`POST /api/reservations`

请求示例：

```json
{
  "expName": "模型船阻力测试",
  "expType": "阻力试验",
  "teacherId": 2001,
  "startTime": "2026-05-29 09:00:00",
  "endTime": "2026-05-29 11:00:00",
  "purpose": "验证模型船阻力变化规律",
  "planSummary": "使用拖曳水池和 IMU 设备进行低速阻力测试",
  "resources": [
    {
      "resourceId": 3001,
      "resourceType": "POOL",
      "quantity": 1,
      "startTime": "2026-05-29 09:00:00",
      "endTime": "2026-05-29 11:00:00",
      "remark": "拖曳水池"
    },
    {
      "resourceId": 3002,
      "resourceType": "SENSOR",
      "quantity": 1,
      "startTime": "2026-05-29 09:00:00",
      "endTime": "2026-05-29 11:00:00",
      "remark": "IMU 传感器"
    }
  ]
}
```

规则：

1. 创建后状态为 `DRAFT`。
2. 主表和明细表必须在同一事务保存。

## 4.4 修改预约草稿

`PUT /api/reservations/{id}`

规则：

1. 仅 `DRAFT` 或 `REJECTED` 状态允许修改后再次提交。
2. 修改时应整体重算资源明细。

## 4.5 提交预约

`POST /api/reservations/{id}/submit`

规则：

1. 仅 `DRAFT` 或已修改后的 `REJECTED` 预约允许提交。
2. 提交时执行资源冲突预校验。
3. 提交成功后状态变更为 `PENDING_TEACHER`。

## 4.6 教师审核

`POST /api/reservations/{id}/teacher-review`

请求示例：

```json
{
  "approved": true,
  "comment": "方案合理，可以进入主任审批"
}
```

规则：

1. 仅 `PENDING_TEACHER` 状态允许审核。
2. 审核通过后变更为 `PENDING_DIRECTOR`。
3. 驳回时状态改为 `REJECTED`，并写入驳回原因。

## 4.7 主任审批

`POST /api/reservations/{id}/director-approve`

请求示例：

```json
{
  "approved": true,
  "comment": "资源安排无冲突，同意执行"
}
```

规则：

1. 仅 `PENDING_DIRECTOR` 状态允许审批。
2. 审批前必须再次执行资源冲突终校验。
3. 审批通过后状态改为 `APPROVED`，并自动生成 `EXPERIMENT_TASK`。
4. 驳回时状态改为 `REJECTED`。

## 4.8 取消预约

`POST /api/reservations/{id}/cancel`

规则：

1. `PENDING_TEACHER`、`PENDING_DIRECTOR` 可由申请人取消。
2. `APPROVED` 后是否允许取消可在课程设计阶段先限制为“不允许前端直接取消”。

---

## 5. 资源接口

## 5.1 查询资源列表

`GET /api/resources`

建议参数：

| 参数 | 说明 |
| --- | --- |
| `resourceType` | 资源类型 |
| `status` | 资源状态 |
| `keyword` | 名称关键字 |

## 5.2 查询资源详情

`GET /api/resources/{id}`

## 5.3 新增资源

`POST /api/resources`

## 5.4 修改资源

`PUT /api/resources/{id}`

## 5.5 更新资源状态

`PUT /api/resources/{id}/status`

请求示例：

```json
{
  "status": "MAINTENANCE",
  "comment": "例行维护"
}
```

## 5.6 删除资源

`DELETE /api/resources/{id}`

规则：

1. 默认执行逻辑删除或状态改为 `DISABLED`。
2. 若已存在历史预约引用，不执行物理删除。

---

## 6. 试验任务接口

## 6.1 查询任务列表

`GET /api/experiments`

## 6.2 查询任务详情

`GET /api/experiments/{id}`

## 6.3 准备完成

`POST /api/experiments/{id}/ready`

规则：

1. `PENDING_PREPARE` 才能流转到 `READY`。

## 6.4 启动试验

`POST /api/experiments/{id}/start`

规则：

1. `READY` 才能启动。
2. 启动后任务状态变为 `RUNNING`。
3. 相关资源状态从 `RESERVED` 变为 `IN_USE`。

## 6.5 完成试验

`POST /api/experiments/{id}/finish`

规则：

1. `RUNNING` 才能完成。
2. 完成后状态变为 `COMPLETED`。

## 6.6 归档试验

`POST /api/experiments/{id}/archive`

规则：

1. `COMPLETED` 才能归档。
2. 归档后状态变为 `ARCHIVED`。

## 6.7 轨迹回放

`GET /api/experiments/{id}/replay`

返回内容建议包含：

1. 轨迹点列表。
2. 关键传感器时间序列。
3. 告警点列表。

---

## 7. 告警接口

## 7.1 查询告警列表

`GET /api/alarms`

建议参数：

| 参数 | 说明 |
| --- | --- |
| `experimentId` | 试验任务 ID |
| `handleStatus` | 处理状态 |
| `alarmType` | 告警类型 |

## 7.2 处理告警

`POST /api/alarms/{id}/handle`

请求示例：

```json
{
  "handleStatus": "RESOLVED",
  "comment": "现场已更换备用电池"
}
```

---

## 8. 文件与归档接口

## 8.1 上传文件

`POST /api/files/upload`

表单字段建议：

1. `experimentId`
2. `file`
3. `fileType`

## 8.2 下载文件

`GET /api/files/{id}/download`

## 8.3 查询试验文件列表

`GET /api/files`

---

## 9. AI 报告接口

## 9.1 查询分析模式

`GET /api/ai/mode`

返回 `analysisMode`（Mock / DeepSeek API）、`mockAi`、`hasApiKey`、`modelName`。

## 9.2 试验数据摘要（生成前预览）

`GET /api/ai/reports/summary/{experimentId}`

聚合传感器极值、告警列表，供前端展示。

## 9.3 生成 AI 报告

`POST /api/ai/reports/generate`

请求示例：

```json
{
  "experimentId": 1001,
  "analysisType": "OVERVIEW"
}
```

`analysisType` 可选：`OVERVIEW` | `ANOMALY` | `RISK` | `SUGGESTION`。

规则：

1. 仅 `COMPLETED` 或 `ARCHIVED` 的试验任务允许生成。
2. 后端先聚合结构化摘要，再调用 DeepSeek API 或 Mock 模板。
3. 重新生成会软删除旧报告；每次调用写入 `AI_CALL_LOG`。

## 9.4 查询试验 AI 报告

`GET /api/ai/reports/{experimentId}`

返回 `sections` 五段结构及 `analysisMode`。

## 9.5 报告列表

`GET /api/ai/reports/list`

## 9.6 AI 调用日志

`GET /api/ai/logs?experimentId=&page=&pageSize=`

## 9.7 删除 AI 报告

`DELETE /api/ai/reports/{id}`

规则：

1. 默认逻辑删除。

---

## 10. WebSocket 接口

## 10.1 连接地址

`/ws/monitor/{experiment_id}`

## 10.2 推送内容

1. 模型船位置。
2. 速度、姿态、电量、阻力。
3. 告警信息。
4. 设备状态变化。

## 10.3 推送消息示例

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
  "resistance": 35.6,
  "alarm": null
}
```

---

## 11. 后端实现建议

建议由以下 Service 负责核心能力：

1. `AuthService`
2. `ReservationService`
3. `ResourceService`
4. `ExperimentService`
5. `MonitorService`
6. `AlarmService`
7. `AiService`

其中：

1. `ReservationService` 负责草稿保存、提交校验、审批流转、任务生成。
2. `ExperimentService` 负责任务状态流转与归档。
3. `MonitorService` 负责实时数据生成、入库和 WebSocket 推送。
4. `AiService` 负责摘要组装、DeepSeek 调用和报告保存。
