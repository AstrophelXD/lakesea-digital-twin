import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ["DATABASE_URL"] = "sqlite:///./test_lakesea.db"
os.environ["MOCK_AI"] = "true"

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import SysRole, SysUser, SysUserRole  # noqa: E402

TEST_DB = BACKEND / "test_lakesea.db"
engine = create_engine(
    f"sqlite:///{TEST_DB}",
    connect_args={"check_same_thread": False},
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    if TEST_DB.exists():
        TEST_DB.unlink()
    from app.models import archive, experiment, monitor, reservation, resource, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        roles = [
            SysRole(role_code="ADMIN", role_name="管理员"),
            SysRole(role_code="STUDENT", role_name="学生"),
            SysRole(role_code="TEACHER", role_name="教师"),
            SysRole(role_code="DIRECTOR", role_name="主任"),
        ]
        for r in roles:
            db.add(r)
        db.flush()
        admin = SysUser(
            username="admin",
            password_hash=hash_password("123456"),
            real_name="管理员",
            status="ACTIVE",
            is_deleted=0,
        )
        student = SysUser(
            username="student01",
            password_hash=hash_password("123456"),
            real_name="学生",
            status="ACTIVE",
            is_deleted=0,
        )
        db.add_all([admin, student])
        db.flush()
        role_map = {r.role_code: r.id for r in db.query(SysRole).all()}
        db.add(SysUserRole(user_id=admin.id, role_id=role_map["ADMIN"]))
        db.add(SysUserRole(user_id=student.id, role_id=role_map["STUDENT"]))
        db.commit()
    finally:
        db.close()
    yield
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    return resp.json()["data"]["token"]
