"""端到端冒烟测试。用法：cd backend && python -m scripts.smoke_test"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

BASE = "http://127.0.0.1:8000"


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=30.0)
    steps: list[str] = []

    def check(name: str, resp: httpx.Response) -> None:
        body = resp.json()
        if body.get("code") != 200:
            raise RuntimeError(f"{name} 失败: {body}")
        steps.append(f"✓ {name}")

    # 1. 健康检查
    check("健康检查", client.get("/api/health"))
    check("数据库健康", client.get("/api/health/db"))

    # 2. 登录
    login = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    check("管理员登录", login)
    token = login.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. 驾驶舱
    check("驾驶舱摘要", client.get("/api/dashboard/summary", headers=headers))

    # 4. 用户列表
    check("用户列表", client.get("/api/users", headers=headers))

    # 5. 资源列表
    check("资源列表", client.get("/api/resources", headers=headers))

    # 6. 预约列表
    check("预约列表", client.get("/api/reservations", headers=headers))

    print("冒烟测试通过：")
    for s in steps:
        print(s)


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("错误：无法连接后端，请先启动 uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as exc:
        print(f"冒烟测试失败：{exc}")
        sys.exit(1)
