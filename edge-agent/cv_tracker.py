"""OpenCV 目标识别（演示版，无 OpenCV 时使用几何模拟）。"""

from __future__ import annotations

POOL_W, POOL_H = 40.0, 20.0


class CvTracker:
    def detect(self, frame: dict, index: int) -> dict:
        cx, cy = frame["cx"], frame["cy"]
        w, h = frame["width"], frame["height"]
        bw, bh = 60, 40
        pool_x = cx / w * POOL_W
        pool_y = (1 - cy / h) * POOL_H
        return {
            "bbox": [cx - bw / 2, cy - bh / 2, bw, bh],
            "centerX": cx,
            "centerY": cy,
            "poolX": round(pool_x, 2),
            "poolY": round(max(0, pool_y), 2),
            "confidence": 0.91,
            "source": "edge-agent",
        }
