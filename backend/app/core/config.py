from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LakeSea Digital Twin"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./lakesea.db"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    upload_dir: str = "uploads"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    mock_ai: bool = True

    # MQTT 模拟接入（默认关闭，使用 WebSocket 内置模拟）
    enable_mqtt: bool = False
    mqtt_broker_host: str = "127.0.0.1"
    mqtt_broker_port: int = 1883
    mqtt_topic_prefix: str = "lakesea/experiment"
    mqtt_client_id: str = "lakesea-backend"
    mqtt_username: str = ""
    mqtt_password: str = ""

    # 视频监控（课程演示：本地文件 / MJPEG / RTSP 占位）
    video_mode: str = "file"
    video_camera_id: str = "CAM-001"
    video_rtsp_url: str = ""

    # 边缘端模拟在线状态
    edge_agent_online: bool = True

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
