"""
模拟 MQTT 传感器发布器：向 Broker 推送试验监控帧，供后端 MQTT 接入消费。

用法：
  cd backend
  python -m scripts.mock_mqtt_publisher --experiment-id 1

需先：
  1. 启动 MQTT Broker（如 Mosquitto，默认 127.0.0.1:1883）
  2. backend/.env 设置 ENABLE_MQTT=true 并重启后端
  3. 监控页对目标试验点击「开始监控」
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.models.constants import POOL_HEIGHT, POOL_WIDTH


@dataclass
class PubState:
    x: float = 10.0
    y: float = 10.0
    heading: float = 45.0
    speed: float = 1.5
    roll: float = 0.0
    pitch: float = 0.0
    battery: float = 100.0
    resistance: float = 30.0


def step_state(state: PubState) -> dict:
    rad = math.radians(state.heading)
    state.x += state.speed * 0.5 * math.cos(rad) + random.uniform(-0.1, 0.1)
    state.y += state.speed * 0.5 * math.sin(rad) + random.uniform(-0.1, 0.1)

    if state.x <= 0 or state.x >= POOL_WIDTH:
        state.heading = (180 - state.heading) % 360
        state.x = max(0.5, min(POOL_WIDTH - 0.5, state.x))
    if state.y <= 0 or state.y >= POOL_HEIGHT:
        state.heading = (-state.heading) % 360
        state.y = max(0.5, min(POOL_HEIGHT - 0.5, state.y))

    state.heading = (state.heading + random.uniform(-8, 8)) % 360
    state.speed = max(0.5, min(3.5, state.speed + random.uniform(-0.15, 0.15)))
    state.roll = max(-25, min(25, state.roll + random.uniform(-2, 2)))
    state.pitch = max(-15, min(15, state.pitch + random.uniform(-1, 1)))
    state.battery = max(5, state.battery - random.uniform(0.3, 0.8))
    state.resistance = max(10, min(60, state.resistance + random.uniform(-3, 3)))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "experimentId": None,
        "shipCode": "M-001",
        "timestamp": now,
        "position": {"x": round(state.x, 2), "y": round(state.y, 2)},
        "speed": round(state.speed, 2),
        "heading": round(state.heading, 2),
        "roll": round(state.roll, 2),
        "pitch": round(state.pitch, 2),
        "battery": round(state.battery, 2),
        "resistance": round(state.resistance, 2),
    }


def build_topic(prefix: str, experiment_id: int) -> str:
    return f"{prefix.rstrip('/')}/{experiment_id}/sensor"


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="模拟 MQTT 传感器数据发布")
    parser.add_argument("--experiment-id", type=int, required=True, help="试验任务 ID")
    parser.add_argument("--host", default=settings.mqtt_broker_host, help="MQTT Broker 地址")
    parser.add_argument("--port", type=int, default=settings.mqtt_broker_port, help="MQTT Broker 端口")
    parser.add_argument(
        "--topic-prefix",
        default=settings.mqtt_topic_prefix,
        help="主题前缀，实际主题为 {prefix}/{experimentId}/sensor",
    )
    parser.add_argument("--interval", type=float, default=1.0, help="发布间隔（秒）")
    parser.add_argument("--count", type=int, default=0, help="发布帧数，0 表示持续发布")
    args = parser.parse_args()

    topic = build_topic(args.topic_prefix, args.experiment_id)
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1,
        client_id="lakesea-mock-publisher",
        protocol=mqtt.MQTTv311,
    )
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password or None)

    print(f"连接 MQTT {args.host}:{args.port} ...")
    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()

    state = PubState()
    sent = 0
    print(f"向 {topic} 发布数据，间隔 {args.interval}s（Ctrl+C 停止）")

    try:
        while args.count == 0 or sent < args.count:
            payload = step_state(state)
            payload["experimentId"] = args.experiment_id
            body = json.dumps(payload, ensure_ascii=False)
            client.publish(topic, body, qos=0)
            sent += 1
            print(f"[{sent}] {payload['timestamp']} pos=({payload['position']['x']}, {payload['position']['y']})")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n已停止发布")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
