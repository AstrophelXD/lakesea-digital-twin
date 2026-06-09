"""MQTT 数据发布。"""

from __future__ import annotations

import json
from typing import Any


class MqttPublisher:
    def __init__(self, host: str, port: int, experiment_id: int) -> None:
        self.host = host
        self.port = port
        self.experiment_id = experiment_id
        self._client = None
        self._connected = False

    def connect(self) -> None:
        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            self._client.connect(self.host, self.port, 60)
            self._client.loop_start()
            self._connected = True
        except Exception as exc:
            print(f"[MQTT] 连接失败: {exc}")
            self._connected = False

    def publish_track(self, payload: dict[str, Any]) -> bool:
        if not self._connected or self._client is None:
            return False
        topic = f"lakesea/experiment/{self.experiment_id}/cv"
        body = json.dumps(payload, ensure_ascii=False)
        result = self._client.publish(topic, body, qos=1)
        return result.rc == 0
