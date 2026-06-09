# 智能中控台与视频感知

监控页已从「2.5D 动画演示」升级为**试验场智能中控台**，体现 B14 要求的视频感知、OpenCV 识别、设备控制、延迟监测与边缘计算架构（课程阶段以可演示模拟为主）。

## 页面布局

```text
顶部：SystemStatusBar（WebSocket / MQTT / 视频流 / 边缘端 / 延迟）
左侧：ControlPanel（设备列表 + 控制指令 + 指令日志）
中间：VideoPanel（视频感知）+ TwinScene（数字孪生水池）
右侧：实时指标 + 系统健康 + 告警
底部：SensorChart（速度/姿态/阻力/电量曲线）
```

## 视频三种模式

| 模式 | 说明 |
|------|------|
| **模拟画面** | Canvas 动画，默认，答辩最稳 |
| **MJPEG 流** | `GET /api/video/{id}/mjpeg`，可接 MediaMTX / FFmpeg |
| **本地 MP4** | `assets/videos/demo_pool.mp4` 或 `uploads/videos/demo_pool.mp4` |

### 生成演示 MP4

```bash
cd backend
python -m scripts.generate_demo_video
```

生成后监控页 VideoPanel 可切换到「本地 MP4」。

## OpenCV 模型船识别

- 接口：`POST /api/cv/{experimentId}/start|stop`，`GET .../track`
- 有 OpenCV：HSV 颜色轮廓识别；无 OpenCV：几何轨迹模拟
- 识别结果经 WebSocket 推送（`type: cv_track`），可驱动数字孪生小船（「CV 驱动孪生」开关）

## 设备控制链路

```text
前端 ControlPanel
    → POST /api/devices/{deviceId}/commands
    → DEVICE_COMMAND_LOG 入库
    → MQTT 发布 lakesea/device/{deviceId}/command（ENABLE_MQTT=true）
    → mock_device_agent 回执 lakesea/device/{deviceId}/status
    → 后端订阅并 WebSocket 广播 device_status
    → ControlPanel 实时更新回执
```

### MQTT 设备演示

```bash
# 终端 1：Broker（如 Mosquitto）
# 终端 2：后端 ENABLE_MQTT=true
# 终端 3：模拟设备
cd backend
python -m scripts.mock_device_agent --device-id DEV-WAVE-001
```

未启用 MQTT 时，指令仍入库并在前端显示 `EXECUTED` 模拟回执。

## 系统健康与延迟

- `GET /api/health/system`：后端 / 数据库 / MQTT / 视频流 / 边缘端
- 监控帧含 `serverTime`，前端计算 WebSocket 延迟

## 边缘 Agent（架构演示）

```text
edge-agent/
├── main.py
├── camera_reader.py
├── cv_tracker.py
├── mqtt_publisher.py
└── offline_buffer.py
```

```bash
cd edge-agent
python main.py --experiment-id 1
```

## 数据库表

- `VIDEO_RECORD`：视频录制会话
- `DEVICE_COMMAND_LOG`：设备指令日志

达梦环境请执行更新后的 `scripts/init_db.sql`；SQLite 开发库 ORM 自动建表。

## 答辩话术

> 视频画面负责**感知层**，数字孪生场景负责**态势层**，两者通过时间戳与模型船坐标关联。边缘端负责采集与预处理，中心端负责业务管理与归档，WebSocket 负责低延迟展示，MQTT 负责设备指令与状态回传。
