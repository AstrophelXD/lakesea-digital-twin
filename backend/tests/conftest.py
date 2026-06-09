import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ["DATABASE_URL"] = "sqlite:///./test_lakesea.db"
os.environ["MOCK_AI"] = "true"

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.resource import LabResource  # noqa: E402
from app.models.user import SysRole, SysUser, SysUserRole  # noqa: E402
from tests.helpers import login  # noqa: E402

TEST_DB = BACKEND / "test_lakesea.db"
engine = create_engine(
    f"sqlite:///{TEST_DB}",
    connect_args={"check_same_thread": False},
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_users_and_resources(db) -> dict[str, int]:
    roles = [
        SysRole(role_code="ADMIN", role_name="管理员"),
        SysRole(role_code="STUDENT", role_name="学生"),
        SysRole(role_code="TEACHER", role_name="教师"),
        SysRole(role_code="DIRECTOR", role_name="主任"),
        SysRole(role_code="MAINTAINER", role_name="维护"),
    ]
    for r in roles:
        db.add(r)
    db.flush()
    role_map = {r.role_code: r.id for r in db.scalars(select(SysRole)).all()}

    users_spec = [
        ("admin", "管理员", "ADMIN"),
        ("student01", "学生甲", "STUDENT"),
        ("teacher01", "李老师", "TEACHER"),
        ("director01", "王主任", "DIRECTOR"),
    ]
    user_ids: dict[str, int] = {}
    for username, real_name, role_code in users_spec:
        user = SysUser(
            username=username,
            password_hash=hash_password("123456"),
            real_name=real_name,
            status="ACTIVE",
            is_deleted=0,
        )
        db.add(user)
        db.flush()
        user_ids[username] = user.id
        db.add(SysUserRole(user_id=user.id, role_id=role_map[role_code]))

    resources_spec = [
        ("POOL-01", "拖曳水池 A", "POOL", "AVAILABLE"),
        ("SHIP-M001", "模型船 M-001", "SHIP", "AVAILABLE"),
    ]
    resource_ids: dict[str, int] = {}
    for code, name, rtype, status in resources_spec:
        res = LabResource(
            resource_code=code,
            resource_name=name,
            resource_type=rtype,
            status=status,
            is_deleted=0,
        )
        db.add(res)
        db.flush()
        resource_ids[code] = res.id

    db.commit()
    return {
        "admin_id": user_ids["admin"],
        "student_id": user_ids["student01"],
        "teacher_id": user_ids["teacher01"],
        "director_id": user_ids["director01"],
        "pool_id": resource_ids["POOL-01"],
        "ship_id": resource_ids["SHIP-M001"],
    }


SEED_IDS: dict[str, int] = {}


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    global SEED_IDS
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()
    from app.models import archive, audit, experiment, monitor, reservation, resource, user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        SEED_IDS = _seed_users_and_resources(db)
    finally:
        db.close()
    yield
    app.dependency_overrides.clear()
    engine.dispose()
    try:
        if TEST_DB.exists():
            TEST_DB.unlink()
    except OSError:
        pass


@pytest.fixture(scope="session")
def ids():
    return SEED_IDS


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
    return login(client, "admin")


@pytest.fixture()
def student_token(client):
    return login(client, "student01")


@pytest.fixture()
def teacher_token(client):
    return login(client, "teacher01")


@pytest.fixture()
def director_token(client):
    return login(client, "director01")
