# 报告截图清单

按评分点准备以下截图，避免临时找材料。

## 前端页面

- [ ] 登录页（不同角色账号列表备注）
- [ ] 首页驾驶舱（统计卡片 + 图表 + 数据库类型）
- [ ] 用户管理页（仅 ADMIN 可见）
- [ ] 操作日志页（筛选 + 表格，仅 ADMIN）
- [ ] 试验预约列表 + 主从表详情弹窗
- [ ] 资源冲突检测提示
- [ ] 审批流程步骤条 + 审批日志时间线
- [ ] 数字孪生监控四区布局 + WebSocket 状态 + 数据源标签
- [ ] （可选）MQTT 模式：Broker 已连接 + mock_mqtt_publisher 运行
- [ ] 模型船运动 + 告警高亮
- [ ] 试验归档：历史列表 + 时间轴播放 + 告警标记
- [ ] 试验归档：导出 CSV/JSON + AI 报告导出
- [ ] 试验归档：文件上传（报告/原始数据/视频）
- [ ] AI 分析工作流 + 数据摘要 + 五段报告 + 调用日志表
- [ ] Mock/DeepSeek 模式标识

## 后端与架构

- [ ] Swagger API 文档页 `/docs`
- [ ] API 层代码（如 `reservation_api.py`）
- [ ] Service 层代码（如 `reservation_service.py`）
- [ ] Repository 层代码（如 `reservation_repository.py`）
- [ ] SQLAlchemy Model（如 `reservation.py` 主从表）

## 达梦 DM8

- [ ] 达梦管理工具连接界面
- [ ] 表结构截图（含外键约束）
- [ ] `EXP_RESERVATION` / `EXP_RESERVATION_RESOURCE` 主从表数据
- [ ] `EXPERIMENT_TASK`、`ALARM_RECORD`、`AI_REPORT`、`AI_CALL_LOG`、`SYS_OPERATION_LOG` 数据
- [ ] 页面数据与库表数据对比

## 接口与实时

- [ ] `GET /api/health/db` 返回达梦 DM8
- [ ] DeepSeek 配置截图（`.env` 中 Key 打码）
- [ ] WebSocket 监控消息（浏览器 Network / 页面实时刷新）

## 测试

- [ ] `pytest` 通过截图
- [ ] `npm run build` 通过截图
- [ ] `python -m scripts.smoke_test` 通过截图
- [ ] `python -m scripts.reset_demo_db --full` 输出（3 预约 / 80 传感器 / AI 报告）
