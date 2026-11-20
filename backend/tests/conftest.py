import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db, make_engine
from app.main import app
from app.models import Role, User
from app.rate_limit import login_limiter
from app.security import hash_password

TEST_PASSWORD = "TestingOnly123"


@pytest.fixture
def db(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        for role in ("employee", "manager", "admin", "vendor"):
            session.add(Role(name=role))
        session.flush()
        password_hash = hash_password(TEST_PASSWORD)
        for role in ("admin", "manager", "employee", "vendor"):
            session.add(
                User(
                    full_name=role.title(),
                    email=f"{role}@company.com",
                    role=role,
                    password_hash=password_hash,
                )
            )
        session.commit()
        session.get(User, 3).manager_id = 2
        session.commit()
        yield session
    engine.dispose()


@pytest.fixture
def client(db):
    login_limiter.buckets.clear()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def headers(client):
    def login(role):
        response = client.post(
            "/api/v1/auth/login", json={"email": f"{role}@company.com", "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return login
