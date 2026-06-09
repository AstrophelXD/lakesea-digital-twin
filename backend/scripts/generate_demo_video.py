"""生成监控页演示视频 uploads/videos/demo_pool.mp4。

用法（在 backend 目录）：
    python -m scripts.generate_demo_video

优先 OpenCV，其次 ffmpeg；均不可用时打印手动说明。
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = BACKEND_ROOT / "uploads" / "videos" / "demo_pool.mp4"
ASSETS_OUTPUT = BACKEND_ROOT / "assets" / "videos" / "demo_pool.mp4"

W, H, FPS, SECONDS = 640, 360, 10, 12


def _ensure_dir() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def generate_with_opencv() -> bool:
    try:
        import cv2
        import numpy as np
    except ImportError:
        return False

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(OUTPUT), fourcc, FPS, (W, H))
    if not writer.isOpened():
        return False

    total = FPS * SECONDS
    for i in range(total):
        t = i / FPS
        img = np.full((H, W, 3), (110, 74, 12), dtype=np.uint8)  # BGR pool blue
        cv2.rectangle(img, (0, H - 36), (W, H), (140, 100, 20), -1)
        cv2.putText(
            img,
            "LakeSea Demo Pool",
            (14, H - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 230, 200),
            1,
        )
        cx = int(W * (0.3 + 0.4 * (0.5 + 0.5 * math.sin(t * 0.8))))
        cy = int(H * (0.52 + 0.18 * math.cos(t * 0.6)))
        cv2.rectangle(img, (cx - 28, cy - 14), (cx + 28, cy + 14), (255, 200, 0), -1)
        cv2.rectangle(img, (cx - 30, cy - 16), (cx + 30, cy + 16), (0, 220, 255), 2)
        writer.write(img)
    writer.release()
    return OUTPUT.exists() and OUTPUT.stat().st_size > 0


def generate_with_ffmpeg() -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    # 用 drawbox 动画模拟模型船
    vf = (
        f"drawbox=x='320+120*sin(t*0.8)-30':y='180+40*cos(t*0.6)-15':"
        f"w=60:h=30:color=yellow@0.9:t=fill,"
        f"drawtext=text='LakeSea Demo Pool':x=14:y=h-28:fontsize=18:fontcolor=white"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x0c4a6e:s={W}x{H}:d={SECONDS}:r={FPS}",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(OUTPUT),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return OUTPUT.exists() and OUTPUT.stat().st_size > 0


def main() -> int:
    _ensure_dir()
    ASSETS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if generate_with_opencv():
        if ASSETS_OUTPUT != OUTPUT and OUTPUT.exists():
            ASSETS_OUTPUT.write_bytes(OUTPUT.read_bytes())
        print(f"已生成（OpenCV）: {OUTPUT}")
        if ASSETS_OUTPUT.exists():
            print(f"已同步到: {ASSETS_OUTPUT}")
        return 0
    if generate_with_ffmpeg():
        if ASSETS_OUTPUT != OUTPUT and OUTPUT.exists():
            ASSETS_OUTPUT.write_bytes(OUTPUT.read_bytes())
        print(f"已生成（ffmpeg）: {OUTPUT}")
        return 0
    print("未能自动生成 demo_pool.mp4。请任选其一：")
    print("  pip install opencv-python-headless")
    print("  或安装 ffmpeg 后重试")
    print(f"  或手动将 mp4 放入 {OUTPUT.parent}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
