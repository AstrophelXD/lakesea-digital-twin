"""模拟设备端：订阅 MQTT 指令并打印执行结果。

运行：python -m scripts.mock_device_agent --device-id DEV-WAVE-001
"""

from __future__ import annotations

import argparse
import json
import time

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise SystemExit("请先安装 paho-mqtt: pip install paho-mqtt")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-id", default="DEV-WAVE-001")
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()

    topic_cmd = f"lakesea/device/{args.device_id}/command"
    topic_status = f"lakesea/device/{args.device_id}/status"

    def on_connect(client, userdata, flags, rc):  # noqa: ARG001
        print(f"[Device {args.device_id}] 已连接 Broker, rc={rc}")
        client.subscribe(topic_cmd)

    def on_message(client, userdata, msg):  # noqa: ARG001
        body = json.loads(msg.payload.decode())
        print(f"[Device {args.device_id}] 收到指令: {body}")
        ack = {
            "deviceId": args.device_id,
            "commandType": body.get("commandType"),
            "status": "EXECUTED",
            "executedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        client.publish(topic_status, json.dumps(ack, ensure_ascii=False), qos=1)
        print(f"[Device {args.device_id}] 已回执 EXECUTED")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"mock-{args.device_id}")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.broker, args.port, 60)
    print(f"[Device {args.device_id}] 监听 {topic_cmd}")
    client.loop_forever()


if __name__ == "__main__":
    main()
