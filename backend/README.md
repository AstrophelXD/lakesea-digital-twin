# 后端（FastAPI）

## 快速启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip-install.bat
:: 或: pip install -r requirements.txt --proxy http://127.0.0.1:7897
:: 测试（可选）: pip install -r requirements-dev.txt --proxy http://127.0.0.1:7897
copy .env.example .env
python -m scripts.seed_db
uvicorn app.main:app --reload
```

### 答辩前一键重置（含完整演示数据）

```bash
python -m scripts.reset_demo_db --full
```

答辩前推荐项目根目录 `pre-defense.bat`（含启服）；仅重置用 `reset-demo.bat`。详见 [docs/demo-data.md](../docs/demo-data.md)。

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

## 演示账号

| 用户名 | 角色 | 密码 |
| --- | --- | --- |
| admin | ADMIN | 123456 |
| director01 | DIRECTOR | 123456 |
| teacher01 | TEACHER | 123456 |
| student01 | STUDENT | 123456 |
| maintainer01 | MAINTAINER | 123456 |

## 数据库

- **本地开发**：默认 SQLite（`lakesea.db`），ORM 自动建表。
- **达梦 DM8**：在 `.env` 中配置 `DATABASE_URL`，并在达梦客户端执行 `scripts/init_db.sql`，再运行 `python -m scripts.seed_db`。
