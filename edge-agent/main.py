"""试验场边缘端 Edge Agent（课程演示版）。

职责：采集视频帧 / 模拟传感器 → OpenCV 识别 → 本地缓存 → MQTT 上传。
运行：python main.py --experiment-id 1
"""

from __future__ import annotations

import argparse
import time

from camera_reader import CameraReader
from cv_tracker import CvTracker
from mqtt_publisher import MqttPublisher
from offline_buffer import OfflineBuffer


def main() -> None:
    parser = argparse.ArgumentParser(description="LakeSea Edge Agent")
    parser.add_argument("--experiment-id", type=int, default=1)
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()

    camera = CameraReader()
    tracker = CvTracker()
    buffer = OfflineBuffer()
    mqtt = MqttPublisher(args.broker, args.port, args.experiment_id)

    print(f"[Edge Agent] 启动 experiment={args.experiment_id}")
    mqtt.connect()

    idx = 0
    while True:
        frame = camera.read_frame(idx)
        track = tracker.detect(frame, idx)
        payload = {
            "experimentId": args.experiment_id,
            "cameraId": "CAM-001",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            **track,
        }
        if mqtt.publish_track(payload):
            buffer.clear_pending()
        else:
            buffer.append(payload)
            print("[Edge Agent] 断网，写入本地缓存")
        idx += 1
        time.sleep(0.5)


if __name__ == "__main__":
    main()
