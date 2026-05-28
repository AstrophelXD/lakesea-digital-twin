# 后端（FastAPI）

## 快速启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
copy .env.example .env
python -m scripts.seed_db
uvicorn app.main:app --reload
```

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
