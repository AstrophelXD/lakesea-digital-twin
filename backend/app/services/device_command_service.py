import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.device_command import DeviceCommandLog
from app.models.user import SysUser
from app.repositories.device_repository import DeviceCommandRepository
from app.repositories.experiment_repository import ExperimentRepository
from app.schemas.common import PageResult
from app.schemas.device_schema import DeviceCommandOut, DeviceInfoOut

logger = logging.getLogger(__name__)

MOCK_DEVICES = [
    ("DEV-SHIP-001", "模型船 M-001", "MODEL_SHIP"),
    ("DEV-IMU-001", "IMU 传感器", "SENSOR"),
    ("DEV-CAM-001", "水池摄像头", "CAMERA"),
    ("DEV-WAVE-001", "造波机", "WAVE_MAKER"),
    ("DEV-TOW-001", "拖车系统", "TOW_CAR"),
    ("DEV-EDGE-001", "边缘计算节点", "EDGE_AGENT"),
]


class DeviceCommandService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DeviceCommandRepository(db)
        self.experiment_repo = ExperimentRepository(db)

    def list_devices(self, experiment_id: Optional[int] = None) -> List[DeviceInfoOut]:
        if experiment_id is not None and not self.experiment_repo.get_by_id(experiment_id):
            raise HTTPException(status_code=404, detail="试验任务不存在")
        online_count = 5 if get_settings().edge_agent_online else 4
        devices: List[DeviceInfoOut] = []
        for idx, (did, name, dtype) in enumerate(MOCK_DEVICES):
            online = idx < online_count
            status = "ONLINE" if online else "OFFLINE"
            if dtype == "WAVE_MAKER" and not online:
                status = "STANDBY"
            devices.append(
                DeviceInfoOut(
                    device_id=did,
                    device_name=name,
                    device_type=dtype,
                    status=status,
                    online=online,
                )
            )
        return devices

    def issue_command(
        self,
        device_id: str,
        command_type: str,
        payload: Optional[dict],
        operator: SysUser,
        experiment_id: Optional[int] = None,
    ) -> DeviceCommandOut:
        known_ids = {d[0] for d in MOCK_DEVICES}
        if device_id not in known_ids:
            raise HTTPException(status_code=404, detail="设备不存在")

        log = self.repo.create(
            DeviceCommandLog(
                device_id=device_id,
                experiment_id=experiment_id,
                command_type=command_type,
                command_payload=DeviceCommandRepository.payload_to_str(payload),
                issued_by=operator.id,
                status="PENDING",
            )
        )
        self.db.flush()
        self._publish_mqtt(device_id, command_type, payload)
        log.status = "EXECUTED"
        log.result_message = f"模拟设备 {device_id} 已执行 {command_type}"
        self.db.commit()
        self.db.refresh(log)
        return DeviceCommandOut.model_validate(log)

    def emergency_stop(
        self, device_id: str, operator: SysUser, experiment_id: Optional[int] = None
    ) -> DeviceCommandOut:
        return self.issue_command(
            device_id,
            "EMERGENCY_STOP",
            {"reason": "operator_triggered"},
            operator,
            experiment_id,
        )

    def list_commands(
        self,
        device_id: str,
        experiment_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[DeviceCommandOut]:
        items, total = self.repo.list_by_device(device_id, experiment_id, page, page_size)
        return PageResult[DeviceCommandOut](
            items=[DeviceCommandOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _publish_mqtt(self, device_id: str, command_type: str, payload: Optional[dict]) -> None:
        settings = get_settings()
        if not settings.enable_mqtt:
            return
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            return
        topic = f"lakesea/device/{device_id}/command"
        body = json.dumps(
            {"commandType": command_type, "payload": payload or {}, "issuedAt": datetime.now().isoformat()},
            ensure_ascii=False,
        )
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            if settings.mqtt_username:
                client.username_pw_set(settings.mqtt_username, settings.mqtt_password or None)
            client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
            client.publish(topic, body, qos=1)
            client.disconnect()
        except Exception as exc:
            logger.warning("MQTT 指令发布失败: %s", exc)
