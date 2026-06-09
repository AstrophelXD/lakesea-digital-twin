# MQTT 模拟接入

本文档说明可选的 MQTT 传感器数据接入方案。系统**默认使用 WebSocket 内置模拟**；开启 MQTT 后，由外部发布器推送数据，后端订阅并写入 `SENSOR_DATA`，同时经 WebSocket 推送给前端。

## 架构对比

```text
默认模式（ENABLE_MQTT=false）
  MonitorService 协程模拟 → WebSocket 广播 → 前端
                        → SENSOR_DATA / SHIP_TRACK

MQTT 模式（ENABLE_MQTT=true）
  mock_mqtt_publisher → MQTT Broker → MqttIngestService 订阅
                                    → WebSocket 广播 → 前端
                                    → SENSOR_DATA / SHIP_TRACK
```

前端始终通过 **WebSocket** 接收实时帧；MQTT 仅替代后端的数据**来源**，不改变监控页交互方式。

## 配置

`backend/.env`：

```env
ENABLE_MQTT=false          # 改为 true 启用 MQTT 接入
MQTT_BROKER_HOST=127.0.0.1
MQTT_BROKER_PORT=1883
MQTT_TOPIC_PREFIX=lakesea/experiment
MQTT_CLIENT_ID=lakesea-backend
# MQTT_USERNAME=
# MQTT_PASSWORD=
```

修改后需**重启后端**。`ENABLE_MQTT=false` 时行为与改造前完全一致。

## 主题与消息格式

### 主题

```
{MQTT_TOPIC_PREFIX}/{experimentId}/sensor
```

示例：`lakesea/experiment/3/sensor`

后端订阅通配符：`lakesea/experiment/+/sensor`

### JSON 载荷

```json
{
  "experimentId": 3,
  "shipCode": "M-001",
  "timestamp": "2026-06-06 14:30:00",
  "position": { "x": 12.5, "y": 8.3 },
  "speed": 1.8,
  "heading": 45.0,
  "roll": 2.1,
  "pitch": 0.5,
  "battery": 92.0,
  "resistance": 35.0
}
```

`experimentId` 可省略，后端会从主题路径解析。

## 演示步骤

### 1. 安装依赖

```bash
cd backend
pip install paho-mqtt
```

### 2. 启动 MQTT Broker

本地可使用 [Mosquitto](https://mosquitto.org/)：

```bash
# Windows：安装后默认监听 127.0.0.1:1883
mosquitto -v
```

无 Broker 时发布器与后端均无法连接，监控页会显示「MQTT 未连接 Broker」。

### 3. 启用 MQTT 并重启后端

```env
ENABLE_MQTT=true
```

### 4. 启动试验与监控

1. 试验任务页：准备 → 启动（状态 `RUNNING`）
2. 数字孪生监控页：选择试验 → 点击 **开始监控**
3. 连接 WebSocket（页面顶部显示「MQTT 接入」）

### 5. 运行模拟发布器

```bash
cd backend
python -m scripts.mock_mqtt_publisher --experiment-id 3
```

可选参数：`--host`、`--port`、`--interval`、`--count`

发布器每秒推送一帧，监控页模型船移动、曲线刷新，数据写入 `SENSOR_DATA`。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/monitor/mqtt/info` | MQTT 开关、Broker 连接状态、订阅主题 |
| GET | `/api/monitor/{id}/status` | 含 `dataSource`、`mqttConnected` |

## 相关文件

| 层级 | 路径 |
|------|------|
| 订阅服务 | `backend/app/services/mqtt_service.py` |
| 监控服务 | `backend/app/services/monitor_service.py` |
| 发布脚本 | `backend/scripts/mock_mqtt_publisher.py` |
| 监控页 | `frontend/src/views/MonitorView.vue` |
| 配置示例 | `backend/.env.example` |

## 答辩说明话术

- **默认演示**：无需 Broker，`ENABLE_MQTT=false`，一键「模拟试验开始」即可。
- **加分演示**：说明系统支持「真实物联网接入扩展」—— 配置 `ENABLE_MQTT=true`，用 `mock_mqtt_publisher` 模拟传感器网关向 MQTT 上报，后端统一入库并经 WebSocket 推送到数字孪生大屏。
