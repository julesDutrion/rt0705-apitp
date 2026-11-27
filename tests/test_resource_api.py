from datetime import date

import pytest

from app.dao import FilmDAO, SupportTypeDAO
from app.models import FilmDTO, SupportTypeDTO, UserRole


@pytest.mark.parametrize(
    ("path", "payload", "idKey", "searchPath"),
    [
        (
            "/actors",
            {"firstName": "Ada", "lastName": "Lovelace"},
            "idActor",
            "/actors?name=Ada",
        ),
        (
            "/directors",
            {"firstName": "Ava", "lastName": "DuVernay"},
            "idDirector",
            None,
        ),
        ("/genres", {"nameGenre": "Drama"}, "idGenre", None),
        (
            "/languages",
            {"code": "fr", "name": "French"},
            "idLanguage",
            "/languages?name=French",
        ),
        (
            "/classifications",
            {"minAge": 12},
            "idClassification",
            "/classifications?minAge=12",
        ),
        (
            "/support-types",
            {"name": "DVD", "mode": "physical"},
            "idSupportType",
            None,
        ),
    ],
)
def test_catalog_rest_resources_support_read_create_update_delete(
    client, make_user, auth_header, path, payload, idKey, searchPath
):
    manager = make_user(UserRole.MANAGER, f"manager-{idKey}")
    headers = auth_header(manager)

    created = client.post(path, json=payload, headers=headers)
    assert created.status_code == 201
    identifier = created.json[idKey]
    assert client.get(path).status_code == 200
    assert client.get(f"{path}/{identifier}").status_code == 200
    if searchPath:
        assert client.get(searchPath).status_code == 200

    updated = client.put(
        f"{path}/{identifier}", json=payload, headers=headers
    )
    assert updated.status_code == 200
    assert client.delete(
        f"{path}/{identifier}", headers=headers
    ).status_code == 204


def test_language_code_lookup_is_public(client, make_user, auth_header):
    manager = make_user(UserRole.MANAGER, "language-manager")
    response = client.post(
        "/languages",
        json={"code": "FR", "name": "French"},
        headers=auth_header(manager),
    )

    assert response.status_code == 201
    assert client.get("/languages/code/fr").json["idLanguage"] == response.json[
        "idLanguage"
    ]


def test_film_rest_resource_supports_create_read_update_and_delete(
    client, make_user, auth_header
):
    manager = make_user(UserRole.MANAGER, "film-manager")
    headers = auth_header(manager)
    payload = {
        "title": "Film",
        "synopsis": "Synopsis",
        "releaseDate": "2020-01-01",
        "duration": 100,
        "posterUrl": "https://example.test/poster.png",
        "addedDate": "2024-01-01",
    }

    created = client.post("/films", json=payload, headers=headers)
    assert created.status_code == 201
    filmId = created.json["idFilm"]
    assert client.get("/films").status_code == 200
    assert client.get(f"/films/{filmId}").status_code == 200

    updated = client.put(
        f"/films/{filmId}",
        json={**payload, "synopsis": "Updated synopsis"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json["synopsis"] == "Updated synopsis"
    assert client.delete(
        f"/films/{filmId}", headers=headers
    ).status_code == 204


def test_support_rest_resource_supports_create_read_update_and_delete(
    client, database, make_user, auth_header
):
    manager = make_user(UserRole.MANAGER, "support-manager")
    headers = auth_header(manager)
    film = FilmDAO(database).createFilm(
        FilmDTO(
            title="Film",
            synopsis="Synopsis",
            releaseDate=date(2020, 1, 1),
            duration=100,
            posterUrl="https://example.test/poster.png",
            addedDate=date(2024, 1, 1),
        )
    )
    supportType = SupportTypeDAO(database).create(
        SupportTypeDTO(name="DVD", mode="physical")
    )
    payload = {
        "idFilm": film.idFilm,
        "idSupportType": supportType.idSupportType,
        "location": "Shelf A",
    }

    created = client.post("/supports", json=payload, headers=headers)
    assert created.status_code == 201
    supportId = created.json["idSupport"]
    assert created.json["isAvailable"] is True
    assert client.get("/supports").status_code == 200
    assert client.get(f"/supports/{supportId}").status_code == 200
    assert client.get(f"/supports/film/{film.idFilm}").status_code == 200

    updated = client.put(
        f"/supports/{supportId}",
        json={**payload, "location": "Shelf B"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json["location"] == "Shelf B"
    assert client.delete(
        f"/supports/{supportId}", headers=headers
    ).status_code == 204


def test_admin_user_routes_cover_login_role_change_and_delete(
    client, make_user, auth_header
):
    admin = make_user(UserRole.ADMIN, "route-admin")
    target = make_user(UserRole.USER, "route-target")
    headers = auth_header(admin)

    assert client.get(
        f"/users/{target.idUser}", headers=headers
    ).status_code == 200
    assert client.get(
        f"/users/login/{target.login}", headers=headers
    ).status_code == 200
    changedRole = client.put(
        f"/users/{target.idUser}/role",
        json={"role": UserRole.MANAGER.value},
        headers=headers,
    )
    assert changedRole.status_code == 200
    assert changedRole.json["role"] == UserRole.MANAGER.value
    assert client.put(
        f"/users/{admin.idUser}/role",
        json={"role": UserRole.USER.value},
        headers=headers,
    ).status_code == 403
    assert client.delete(
        f"/users/{target.idUser}", headers=headers
    ).status_code == 204
