"""断网本地缓存（JSONL）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OfflineBuffer:
    def __init__(self, path: str = "edge_buffer.jsonl") -> None:
        self.path = Path(path)

    def append(self, payload: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def clear_pending(self) -> None:
        if self.path.exists():
            self.path.unlink()
