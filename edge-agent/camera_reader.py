"""摄像头 / 视频文件读取（演示版）。"""

from __future__ import annotations

import math


class CameraReader:
    def read_frame(self, index: int) -> dict:
        t = index * 0.05
        return {
            "width": 640,
            "height": 360,
            "cx": 320 + 120 * math.sin(t),
            "cy": 180 + 40 * math.cos(t * 0.7),
        }
