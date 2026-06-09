from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import engine
from app.core.db_info import check_db_health
from app.services.mqtt_service import mqtt_service


class SystemHealthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_system_status(self, experiment_id: Optional[int] = None) -> dict[str, Any]:
        settings = get_settings()
        db_health = check_db_health(engine, settings.database_url)
        mqtt_enabled = settings.enable_mqtt
        mqtt_connected = mqtt_service.is_connected if mqtt_enabled else None

        latest_data_time: Optional[str] = None
        if experiment_id:
            from app.repositories.sensor_repository import SensorRepository

            sensors = SensorRepository(self.db).list_recent_sensor(experiment_id, 1)
            if sensors:
                latest_data_time = sensors[-1].timestamp.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "backend": "UP",
            "database": "UP" if db_health.connected else "DOWN",
            "databaseType": db_health.database_type,
            "mqttBroker": "UP" if mqtt_connected else ("DISABLED" if not mqtt_enabled else "DOWN"),
            "videoStream": "UP",
            "edgeAgent": "UP" if settings.edge_agent_online else "OFFLINE",
            "mqttEnabled": mqtt_enabled,
            "mqttConnected": mqtt_connected,
            "edgeAgentOnline": settings.edge_agent_online,
            "dataRefreshHz": 1,
            "latestDataTime": latest_data_time,
            "serverTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        }
