# 试验归档与数据回放

## 功能概述

试验归档模块支持对 **已完成 / 已归档** 试验进行数据复盘，体现 B14「视频+数据同步回放」的课程要求（当前阶段以时间轴驱动轨迹与曲线同步，视频以文件占位上传）。

```text
完成试验 → 归档 → 历史试验列表 → 选择试验 → 时间轴回放
  ├─ 模型船轨迹（2.5D 场景）
  ├─ 传感器实时读数
  ├─ 历史曲线定位
  ├─ 告警点标记与跳转
  ├─ 文件管理（报告/原始数据/视频占位）
  └─ 导出 + 联动 AI 报告
```

## 页面结构（ArchiveView）

| 区域 | 说明 |
|------|------|
| 左侧 | 历史试验列表（COMPLETED / ARCHIVED） |
| 右上 | 统计卡片、导出、上传、AI 报告入口 |
| 中间 | 轨迹回放场景（随时间轴推进） |
| 时间轴 | 播放/暂停/重置、Slider、告警 ⚠ 标记 |
| 下方 | 速度/电量/阻力/横摇曲线（ECharts 同步） |
| 底部 | 告警表（可跳转时间点）、试验文件表 |

## 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/experiments?status=COMPLETED` | 已完成试验列表 |
| GET | `/api/experiments?status=ARCHIVED` | 已归档试验列表 |
| GET | `/api/experiments/{id}/replay` | 回放聚合数据 |
| GET | `/api/experiments/{id}/export/sensor-csv` | 导出传感器 CSV |
| GET | `/api/experiments/{id}/export/track-json` | 导出轨迹 JSON |
| GET | `/api/experiments/{id}/export/ai-report?fmt=markdown` | 导出 AI 报告 Markdown |
| GET | `/api/experiments/{id}/export/ai-report?fmt=html` | 导出 AI 报告 HTML |
| POST | `/api/files/upload` | 上传试验文件 |

### 回放数据结构要点

- `sensorSeries`：按时间排序的传感器序列（时间轴主数据）
- `tracks`：模型船轨迹点
- `alarmMarkers`：告警在时间轴上的 `seriesIndex` 定位
- `aiReport`：是否已生成 AI 报告摘要
- `files`：已上传的试验文件

## 演示步骤

1. 完成一次带监控的试验（监控页启动模拟 → 产生传感器/轨迹/告警数据）
2. 试验任务页：**完成试验** → **归档**
3. 打开 **试验归档** 菜单
4. 左侧选择试验，点击 **播放** 或拖动时间轴
5. 观察：模型船移动、曲线 tooltip 同步、告警 ⚠ 标记
6. 点击告警表 **跳转** 定位到告警时刻
7. **导出数据** → 传感器 CSV / 轨迹 JSON
8. 在 **AI 分析** 页生成报告后，回到归档页 **导出 AI 报告**
9. 上传试验报告（类型选「试验报告」）

## 相关代码

```text
frontend/src/views/ArchiveView.vue      # 归档回放页
frontend/src/components/TrackReplay.vue # 轨迹场景组件
frontend/src/api/experiment.ts          # replay + export API
backend/app/services/experiment_service.py   # get_replay
backend/app/services/archive_export_service.py  # 导出
backend/app/api/experiment_api.py       # 路由
```

## 数据来源表

| 回放内容 | 数据库表 |
|----------|----------|
| 传感器曲线 | `SENSOR_DATA` |
| 模型船轨迹 | `SHIP_TRACK` |
| 告警标记 | `ALARM_RECORD` |
| 试验文件 | `EXPERIMENT_FILE` |
| AI 报告 | `AI_REPORT` |
| 任务元信息 | `EXPERIMENT_TASK` |
