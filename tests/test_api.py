from datetime import date, timedelta

from app.dao import (
    ClassificationDAO,
    FilmDAO,
    LoanDAO,
    SupportDAO,
    SupportTypeDAO,
)
from app.models import (
    ClassificationDTO,
    FilmDTO,
    LoanDTO,
    SupportDTO,
    SupportTypeDTO,
    UserRole,
)


def _film(title, classification):
    return FilmDTO(
        title=title,
        synopsis="Synopsis",
        releaseDate=date(2020, 1, 1),
        duration=100,
        posterUrl="https://example.test/poster.png",
        addedDate=date(2024, 1, 1),
        classification=classification,
    )


def test_registration_and_login_hide_password_hash(client):
    body = {
        "login": "reader",
        "email": "reader@example.test",
        "password": "StrongPassword1!",
        "confirmPassword": "StrongPassword1!",
        "birthDate": "1990-01-01",
    }

    created = client.post("/users", json=body)
    assert created.status_code == 201
    assert "passwordHash" not in created.json

    mismatch = client.post(
        "/users", json={**body, "confirmPassword": "DifferentPassword2!"}
    )
    assert mismatch.status_code == 400

    login = client.post(
        "/auth/login",
        json={"login": "reader", "password": "StrongPassword1!"},
    )
    assert login.status_code == 200
    assert "passwordHash" not in login.json["user"]
    assert login.json["tokenType"] == "Bearer"


def test_user_collection_is_admin_only_and_never_returns_password_hash(
    client, make_user, auth_header
):
    regularUser = make_user(UserRole.USER, "reader")
    administrator = make_user(UserRole.ADMIN, "admin")

    assert client.get("/users").status_code == 401
    assert client.get("/users", headers=auth_header(regularUser)).status_code == 403
    response = client.get("/users", headers=auth_header(administrator))

    assert response.status_code == 200
    assert len(response.json) == 2
    assert all("passwordHash" not in user for user in response.json)


def test_users_can_only_update_their_own_profile(client, make_user, auth_header):
    reader = make_user(UserRole.USER, "reader")
    other = make_user(UserRole.USER, "other")
    headers = auth_header(reader)

    denied = client.put(
        f"/users/{other.idUser}",
        json={"login": "changed"},
        headers=headers,
    )
    allowed = client.put(
        f"/users/{reader.idUser}",
        json={"login": "reader-updated"},
        headers=headers,
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json["login"] == "reader-updated"
    assert "passwordHash" not in allowed.json


def test_public_film_routes_filter_by_age_and_reject_invalid_optional_token(
    client, database, make_user, auth_header
):
    classifications = ClassificationDAO(database)
    age12 = classifications.create(ClassificationDTO(minAge=12))
    age18 = classifications.create(ClassificationDTO(minAge=18))
    films = FilmDAO(database)
    films.createFilm(_film("Family film", age12))
    films.createFilm(_film("Mature film", age18))
    birthday = date.today() - timedelta(days=12 * 365 + 5)
    reader = make_user(UserRole.USER, "young-reader", birthday)

    anonymous = client.get("/films")
    filtered = client.get("/films", headers=auth_header(reader))
    familyFilmId = next(
        film["idFilm"]
        for film in anonymous.json
        if film["title"] == "Family film"
    )
    filteredDetail = client.get(
        f"/films/{familyFilmId}",
        headers=auth_header(reader),
    )
    invalidToken = client.get(
        "/films", headers={"Authorization": "Bearer invalid"}
    )

    assert anonymous.status_code == 200
    assert len(anonymous.json) == 2
    assert filtered.status_code == 200
    assert {film["title"] for film in filtered.json} == {"Family film"}
    assert filteredDetail.status_code == 200
    manager = make_user(UserRole.MANAGER, "adult-manager")
    assert client.get(
        "/films", headers=auth_header(manager)
    ).status_code == 200
    assert invalidToken.status_code == 401


def test_loan_routes_enforce_ownership_roles_and_return_availability(
    client, database, make_user, auth_header, monkeypatch
):
    classifications = ClassificationDAO(database)
    classification = classifications.create(ClassificationDTO(minAge=0))
    film = FilmDAO(database).createFilm(_film("Borrowable", classification))
    supportType = SupportTypeDAO(database).create(
        SupportTypeDTO(name="DVD", mode="physical")
    )
    support = SupportDAO(database).create(
        SupportDTO(
            idFilm=film.idFilm,
            idSupportType=supportType.idSupportType,
            location="Shelf A",
        )
    )
    reader = make_user(UserRole.USER, "reader")
    otherReader = make_user(UserRole.USER, "other")
    manager = make_user(UserRole.MANAGER, "manager")

    created = client.post(
        "/loans",
        json={"idPhysicalSupport": support.idSupport},
        headers=auth_header(reader),
    )
    assert created.status_code == 201
    loanId = created.json["idLoan"]
    assert created.json["idUser"] == reader.idUser
    assert created.json["status"] == "IN_PROGRESS"

    assert client.get("/loans").status_code == 401
    assert client.get("/loans", headers=auth_header(reader)).status_code == 403
    assert client.get(
        f"/loans/me/{loanId}", headers=auth_header(otherReader)
    ).status_code == 404
    assert client.get(
        "/loans/me", headers=auth_header(reader)
    ).json[0]["idLoan"] == loanId
    assert client.patch(
        f"/loans/{loanId}/return", headers=auth_header(reader)
    ).status_code == 403

    duplicate = client.post(
        "/loans",
        json={"idPhysicalSupport": support.idSupport},
        headers=auth_header(otherReader),
    )
    assert duplicate.status_code == 409
    assert client.get(
        "/loans", headers=auth_header(manager)
    ).json[0]["idLoan"] == loanId
    assert client.get(
        f"/loans/user/{reader.login}", headers=auth_header(manager)
    ).json[0]["idLoan"] == loanId
    assert client.get(
        f"/loans/{loanId}", headers=auth_header(manager)
    ).json["idLoan"] == loanId

    def returnLoanWithMockMongo(dao, idLoan, returnedAt):
        stored = dao._collection.find_one({"idLoan": idLoan})
        if stored is None or stored.get("actualReturnDate") is not None:
            return None
        dao._collection.update_one(
            {"idLoan": idLoan},
            {"$set": {"actualReturnDate": returnedAt}},
        )
        return LoanDTO.fromDict(dao._collection.find_one({"idLoan": idLoan}))

    monkeypatch.setattr(LoanDAO, "markReturned", returnLoanWithMockMongo)
    returned = client.patch(
        f"/loans/{loanId}/return", headers=auth_header(manager)
    )
    assert returned.status_code == 200
    assert returned.json["status"] == "RETURNED"
    assert returned.json["actualReturnDate"] is not None
    assert client.patch(
        f"/loans/{loanId}/return", headers=auth_header(manager)
    ).status_code == 409
    assert client.get("/supports").json[0]["isAvailable"] is True


def test_catalog_mutations_require_manager_or_admin(client, make_user, auth_header):
    reader = make_user(UserRole.USER, "reader")
    manager = make_user(UserRole.MANAGER, "manager")

    denied = client.post(
        "/actors",
        json={"firstName": "Ada", "lastName": "Lovelace"},
        headers=auth_header(reader),
    )
    created = client.post(
        "/actors",
        json={"firstName": "Ada", "lastName": "Lovelace"},
        headers=auth_header(manager),
    )

    assert denied.status_code == 403
    assert created.status_code == 201
    assert client.get("/actors").status_code == 200
