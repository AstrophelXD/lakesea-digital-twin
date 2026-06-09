# AI 分析报告

本文档说明试验 AI 分析报告的生成工作流、接口与答辩演示要点。

## 功能概览

1. **工作流**：选择试验 → 后端汇总传感器/告警数据 → 选择分析类型 → 生成报告 → 五段结构化展示 → 写入 `AI_REPORT`
2. **分析类型**：`OVERVIEW`（概况摘要）、`ANOMALY`（异常原因）、`RISK`（风险提示）、`SUGGESTION`（后续建议）
3. **双模式**：`MOCK_AI=true` 或无 API Key 时使用本地 Mock；配置 DeepSeek Key 后由后端调用真实 API
4. **调用日志**：每次生成写入 `AI_CALL_LOG`（时间、模型、Mock/API、耗时、Token、失败原因）
5. **归档联动**：归档页可跳转 AI 分析页，并导出 Markdown/HTML 报告

## 页面入口

- 菜单：**AI 分析** → `AiReportView.vue`
- 试验任务 / 归档页：带 `experimentId` 查询参数跳转

## 报告结构

生成结果固定为五段（Mock 模板与 DeepSeek 提示词均要求此结构）：

| 段落 | 说明 |
|------|------|
| 试验概况 | 任务名称、分析类型 |
| 关键数据 | 采样点、速度、电量、阻力、横摇 |
| 异常记录 | 告警数量与类型汇总 |
| 可能原因 | 对告警模式的解释 |
| 改进建议 | 后续试验与阈值策略建议 |

前端 `AiReportPanel.vue` 按 `sections` 数组逐段渲染；历史报告无 `sections` 时回退为摘要 + 分析两段。

## API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ai/mode` | 当前分析模式（Mock / DeepSeek API） |
| GET | `/api/ai/logs` | AI 调用日志分页，可选 `experimentId` |
| GET | `/api/ai/reports/summary/{experimentId}` | 试验数据摘要（生成前预览） |
| GET | `/api/ai/reports/list` | 已生成报告列表 |
| POST | `/api/ai/reports/generate` | 生成报告（body: `experimentId`, `analysisType`） |
| GET | `/api/ai/reports/{experimentId}` | 查询指定试验的最新报告 |
| DELETE | `/api/ai/reports/{reportId}` | 逻辑删除报告 |

### 生成规则

- 仅 `COMPLETED` 或 `ARCHIVED` 状态的试验可生成
- 重新生成会软删除旧报告并写入新记录
- DeepSeek API Key 仅在后端 `.env` 读取，前端不暴露

## 环境配置

`backend/.env`：

```env
MOCK_AI=true
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

答辩演示默认 `MOCK_AI=true` 即可；若需真实 API，设置 Key 并将 `MOCK_AI=false`。

## 数据库表

- **AI_REPORT**：报告正文、`ANALYSIS_TYPE`、`MODEL_NAME`、生成人与时间
- **AI_CALL_LOG**：每次调用的审计记录

达梦环境执行 `backend/scripts/init_db.sql`；本地 SQLite 由 ORM `create_all` 自动建表。若已有旧库缺少新列/表，可删除 `lakesea.db` 后重启后端重建。

## 答辩演示步骤

1. 打开 **AI 分析**，选择已归档试验
2. 查看 **试验关键数据摘要**（采样点、极值、告警列表）
3. 选择分析类型，点击 **生成报告**
4. 确认顶部显示 **Mock / DeepSeek API** 模式标签
5. 查看五段结构化报告
6. 底部 **AI 调用日志** 表出现新记录（耗时、模型、成功/失败）
7. 点击 **跳转归档页**，导出 AI 报告 Markdown 或 HTML

## 相关文件

| 层级 | 路径 |
|------|------|
| 页面 | `frontend/src/views/AiReportView.vue` |
| 组件 | `frontend/src/components/AiReportPanel.vue` |
| API 客户端 | `frontend/src/api/ai.ts` |
| 路由 | `backend/app/api/ai_api.py` |
| 业务 | `backend/app/services/ai_service.py` |
| 模型 | `backend/app/models/archive.py` |
