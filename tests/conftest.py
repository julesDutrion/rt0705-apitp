from datetime import date

import bcrypt
import mongomock
import pytest

from app.app import createApp
from app.dao import UserDAO
from app.models import UserDTO, UserRole


@pytest.fixture
def database():
    client = mongomock.MongoClient()
    return client["videotheque_test"]


@pytest.fixture
def app(database, monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "pytest-only-secret-key-at-least-32-bytes"
    )
    monkeypatch.setenv("SWAGGER_ENABLED", "false")
    return createApp(database=database)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(database):
    def create(role=UserRole.USER, login=None, birth_date=None):
        userDAO = UserDAO(database)
        user = UserDTO(
            role=role,
            login=login or f"user-{role.name.lower()}",
            email=f"{login or role.name.lower()}@example.test",
            passwordHash=bcrypt.hashpw(
                b"StrongPassword1!", bcrypt.gensalt()
            ).decode(),
            birthDate=birth_date or date(1990, 1, 1),
        )
        return userDAO.create(user)

    return create


@pytest.fixture
def auth_header(app):
    def create(user):
        token = app.extensions["authService"].generateToken(user)
        return {"Authorization": f"Bearer {token}"}

    return create
