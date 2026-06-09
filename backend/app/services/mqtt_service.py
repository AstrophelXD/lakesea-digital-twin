import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any, Optional

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.ws_manager import ws_manager
from app.schemas.monitor_schema import MonitorFrame, MqttInfoOut, MqttSensorPayload
from app.services.monitor_service import MonitorService

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - optional until pip install
    mqtt = None  # type: ignore[assignment]


class MqttIngestService:
    """订阅 MQTT 传感器主题，写入 SENSOR_DATA 并经 WebSocket 广播。"""

    def __init__(self) -> None:
        self._client: Any = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._connected = False
        self._topic_re = re.compile(r"/(\d+)/sensor$")

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        settings = get_settings()
        if not settings.enable_mqtt:
            return
        if mqtt is None:
            logger.warning("paho-mqtt 未安装，MQTT 接入已跳过")
            return

        self._loop = loop
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=settings.mqtt_client_id,
            protocol=mqtt.MQTTv311,
        )
        if settings.mqtt_username:
            self._client.username_pw_set(
                settings.mqtt_username,
                settings.mqtt_password or None,
            )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        try:
            self._client.connect(
                settings.mqtt_broker_host,
                settings.mqtt_broker_port,
                keepalive=60,
            )
            self._client.loop_start()
            logger.info(
                "MQTT 客户端已启动 %s:%s",
                settings.mqtt_broker_host,
                settings.mqtt_broker_port,
            )
        except Exception as exc:
            logger.error("MQTT 连接失败: %s", exc)
            self._connected = False

    def stop(self) -> None:
        if self._client is None:
            return
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass
        self._client = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_info(self) -> MqttInfoOut:
        settings = get_settings()
        prefix = settings.mqtt_topic_prefix.rstrip("/")
        return MqttInfoOut(
            enabled=settings.enable_mqtt,
            connected=self._connected,
            broker_host=settings.mqtt_broker_host,
            broker_port=settings.mqtt_broker_port,
            topic_prefix=prefix,
            subscribed_topic=f"{prefix}/+/sensor",
            data_source="mqtt" if settings.enable_mqtt else "websocket_sim",
        )

    def _on_connect(self, _client: Any, _userdata: Any, _flags: Any, rc: int) -> None:
        settings = get_settings()
        if rc != 0:
            logger.error("MQTT 连接被拒绝，rc=%s", rc)
            self._connected = False
            return
        self._connected = True
        topic = f"{settings.mqtt_topic_prefix.rstrip('/')}/+/sensor"
        _client.subscribe(topic, qos=0)
        logger.info("MQTT 已订阅 %s", topic)

    def _on_disconnect(self, _client: Any, _userdata: Any, rc: int) -> None:
        self._connected = False
        if rc != 0:
            logger.warning("MQTT 意外断开，rc=%s", rc)

    def _parse_experiment_id(self, topic: str, payload: MqttSensorPayload) -> int:
        if payload.experiment_id is not None:
            return payload.experiment_id
        match = self._topic_re.search(topic)
        if match:
            return int(match.group(1))
        raise ValueError(f"无法从主题解析试验 ID: {topic}")

    def _on_message(self, _client: Any, _userdata: Any, msg: Any) -> None:
        try:
            raw = json.loads(msg.payload.decode("utf-8"))
            payload = MqttSensorPayload.model_validate(raw)
            experiment_id = self._parse_experiment_id(msg.topic, payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            logger.warning("忽略无效 MQTT 消息: %s", exc)
            return

        runner = MonitorService.get_runner(experiment_id)
        if not runner.running:
            return

        frame = self._to_frame(experiment_id, payload)
        runner.state.frame_count += 1
        try:
            MonitorService.persist_frame(experiment_id, frame)
        except Exception as exc:
            logger.error("MQTT 数据持久化失败: %s", exc)
            return

        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(experiment_id, frame),
                self._loop,
            )

    def _to_frame(self, experiment_id: int, payload: MqttSensorPayload) -> dict[str, Any]:
        ts = payload.timestamp
        if isinstance(ts, datetime):
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = str(ts)

        frame = MonitorFrame(
            experiment_id=experiment_id,
            ship_code=payload.ship_code,
            timestamp=ts_str,
            position={"x": payload.position.x, "y": payload.position.y},
            speed=payload.speed,
            heading=payload.heading,
            roll=payload.roll,
            pitch=payload.pitch,
            battery=payload.battery,
            resistance=payload.resistance,
            alarm=None,
        )
        return frame.model_dump(by_alias=True)


mqtt_service = MqttIngestService()
