from datetime import date
from unittest.mock import MagicMock, Mock

import bcrypt
import pytest
from pymongo.errors import DuplicateKeyError

import bootstrap_admin
from app.models import UserRole


def test_ask_email_retries_invalid_values(monkeypatch, capsys):
    answers = iter(["not-an-email", "admin@example.test"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert bootstrap_admin.askEmail() == "admin@example.test"
    assert "invalide" in capsys.readouterr().out


def test_ask_birth_date_rejects_bad_and_future_dates(monkeypatch, capsys):
    answers = iter(["yesterday", "2999-01-01", "1990-01-01"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert bootstrap_admin.askBirthDate() == date(1990, 1, 1)
    output = capsys.readouterr().out
    assert "Format invalide" in output
    assert "futur" in output


def test_ask_password_requires_complexity_confirmation_and_bcrypt_length(
    monkeypatch, capsys
):
    answers = iter(
        [
            "weak",
            "StrongPassword1!",
            "DifferentPassword2!",
            "StrongPassword1!",
            "StrongPassword1!",
        ]
    )
    monkeypatch.setattr(bootstrap_admin.getpass, "getpass", lambda _prompt: next(answers))

    assert bootstrap_admin.askPassword() == "StrongPassword1!"
    output = capsys.readouterr().out
    assert "au moins 12 caractères" in output
    assert "ne correspondent pas" in output


def test_ask_password_rejects_values_over_bcrypt_byte_limit(monkeypatch, capsys):
    longPassword = "StrongPassword1!" + ("x" * 57)
    answers = iter([longPassword, "StrongPassword1!", "StrongPassword1!"])
    monkeypatch.setattr(
        bootstrap_admin.getpass, "getpass", lambda _prompt: next(answers)
    )

    assert bootstrap_admin.askPassword() == "StrongPassword1!"
    assert "72 octets" in capsys.readouterr().out


def test_create_admin_creates_admin_role_with_hashed_password(monkeypatch):
    dao = Mock()
    dao.getByLogin.return_value = None
    dao.getByEmail.return_value = None
    monkeypatch.setattr(bootstrap_admin, "askEmail", lambda: "admin@example.test")
    monkeypatch.setattr(bootstrap_admin, "askBirthDate", lambda: date(1980, 1, 1))
    monkeypatch.setattr(bootstrap_admin, "askPassword", lambda: "StrongPassword1!")

    bootstrap_admin.createAdmin(dao)

    user = dao.create.call_args.args[0]
    assert user.login == "admin"
    assert user.role is UserRole.ADMIN
    assert bcrypt.checkpw(
        b"StrongPassword1!", user.passwordHash.encode("utf-8")
    )


def test_create_admin_refuses_existing_login_or_email(monkeypatch):
    dao = Mock()
    dao.getByLogin.return_value = object()

    with pytest.raises(SystemExit):
        bootstrap_admin.createAdmin(dao)

    dao.getByLogin.return_value = None
    dao.getByEmail.return_value = object()
    monkeypatch.setattr(bootstrap_admin, "askEmail", lambda: "used@example.test")
    with pytest.raises(ValueError, match="déjà utilisée"):
        bootstrap_admin.createAdmin(dao)


def test_create_admin_translates_duplicate_database_key(monkeypatch):
    dao = Mock()
    dao.getByLogin.return_value = None
    dao.getByEmail.return_value = None
    dao.create.side_effect = DuplicateKeyError("duplicate")
    monkeypatch.setattr(bootstrap_admin, "askEmail", lambda: "admin@example.test")
    monkeypatch.setattr(bootstrap_admin, "askBirthDate", lambda: date(1980, 1, 1))
    monkeypatch.setattr(bootstrap_admin, "askPassword", lambda: "StrongPassword1!")

    with pytest.raises(ValueError, match="déjà utilisé"):
        bootstrap_admin.createAdmin(dao)


def test_main_requires_mongo_credentials(monkeypatch):
    monkeypatch.delenv("MONGO_USERNAME", raising=False)
    monkeypatch.delenv("MONGO_PASSWORD", raising=False)
    monkeypatch.setattr(bootstrap_admin, "MONGO_USERNAME", None)
    monkeypatch.setattr(bootstrap_admin, "MONGO_PASSWORD", None)

    with pytest.raises(RuntimeError, match="Identifiants MongoDB absents"):
        bootstrap_admin.main()


def test_main_pings_database_creates_admin_and_closes_client(monkeypatch):
    client = MagicMock()
    database = Mock()
    client.__getitem__.return_value = database
    userDAO = Mock()
    createAdmin = Mock()
    mongoClientFactory = Mock(return_value=client)
    monkeypatch.setattr(bootstrap_admin, "MONGO_USERNAME", "admin-user")
    monkeypatch.setattr(bootstrap_admin, "MONGO_PASSWORD", "admin-password")
    monkeypatch.setattr(bootstrap_admin, "MONGO_HOST", "127.0.0.1")
    monkeypatch.setattr(bootstrap_admin, "MONGO_PORT", "27017")
    monkeypatch.setattr(bootstrap_admin, "MONGO_DATABASE", "test-db")
    monkeypatch.setattr(bootstrap_admin, "MONGO_AUTH_SOURCE", "admin")
    monkeypatch.setattr(bootstrap_admin, "MongoClient", mongoClientFactory)
    monkeypatch.setattr(bootstrap_admin, "createAdmin", createAdmin)
    monkeypatch.setattr("app.dao.UserDAO", lambda _database: userDAO)

    bootstrap_admin.main()

    client.admin.command.assert_called_once_with("ping")
    createAdmin.assert_called_once_with(userDAO)
    client.close.assert_called_once_with()
    assert mongoClientFactory.call_args.kwargs == {
        "serverSelectionTimeoutMS": 5000
    }


def test_main_closes_client_when_database_ping_fails(monkeypatch):
    from pymongo.errors import PyMongoError

    client = Mock()
    client.admin.command.side_effect = PyMongoError("unavailable")
    monkeypatch.setattr(bootstrap_admin, "MONGO_USERNAME", "admin-user")
    monkeypatch.setattr(bootstrap_admin, "MONGO_PASSWORD", "admin-password")
    monkeypatch.setattr(bootstrap_admin, "MongoClient", Mock(return_value=client))

    with pytest.raises(PyMongoError, match="unavailable"):
        bootstrap_admin.main()
    client.close.assert_called_once_with()
