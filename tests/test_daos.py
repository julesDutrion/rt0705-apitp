from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock

import pytest
from pymongo.errors import DuplicateKeyError

from app.dao import (
    ActorDAO,
    ClassificationDAO,
    DirectorDAO,
    FilmDAO,
    GenreDAO,
    LanguageDAO,
    LoanDAO,
    SupportDAO,
    SupportTypeDAO,
    UserDAO,
)
from app.models import (
    ActorDTO,
    ClassificationDTO,
    DirectorDTO,
    FilmDTO,
    GenreDTO,
    LanguageDTO,
    LoanDTO,
    SupportDTO,
    SupportTypeDTO,
    UserDTO,
    UserRole,
)


@pytest.mark.parametrize(
    ("daoType", "dto", "idField"),
    [
        (ActorDAO, ActorDTO(firstName="Ada", lastName="Lovelace"), "idActor"),
        (DirectorDAO, DirectorDTO(lastName="Nolan", firstName="Christopher"), "idDirector"),
        (GenreDAO, GenreDTO(nameGenre="Drama"), "idGenre"),
        (LanguageDAO, LanguageDTO(code="FR", name="French"), "idLanguage"),
        (ClassificationDAO, ClassificationDTO(minAge=12), "idClassification"),
        (SupportTypeDAO, SupportTypeDTO(name="DVD", mode="physical"), "idSupportType"),
    ],
)
def test_catalog_daos_generate_ids_and_round_trip(database, daoType, dto, idField):
    dao = daoType(database)

    created = dao.create(dto)

    assert getattr(created, idField) == 1
    assert getattr(dao.getById(1), idField) == 1
    assert dao.exists(1)
    assert dao.getAll() == [created]
    assert dao.delete(1)
    assert not dao.exists(1)


def test_language_dao_searches_codes_case_insensitively_and_normalizes_updates(
    database,
):
    dao = LanguageDAO(database)
    language = dao.create(LanguageDTO(code="fr", name="French"))

    assert dao.getByCode("FR") == language
    language.code = "EN"
    assert dao.update(language)
    assert language.code == "en"
    assert dao.getByCode("en").name == "French"


def test_classification_dao_returns_only_valid_ids_allowed_for_age(database):
    collection = database["classifications"]
    collection.insert_many(
        [
            {"idClassification": 1, "minAge": 0},
            {"idClassification": 2, "minAge": 12},
            {"idClassification": 3, "minAge": 18},
            {"idClassification": 4, "minAge": -1},
            {"idClassification": "invalid", "minAge": 10},
            {"idClassification": 6, "minAge": 12.5},
        ]
    )
    dao = ClassificationDAO(database)

    assert dao.getIdsAllowedForAge(12) == [1, 2]


def test_user_dao_persists_role_and_enforces_unique_login(database):
    dao = UserDAO(database)
    user = UserDTO(
        role=UserRole.ADMIN,
        login="admin",
        email="admin@example.test",
        passwordHash="hash",
        birthDate=date(1990, 1, 1),
    )

    dao.create(user)

    assert user.idUser == 1
    assert dao.getByLogin("admin").role is UserRole.ADMIN
    assert dao.getByEmail("admin@example.test").idUser == user.idUser
    with pytest.raises(DuplicateKeyError):
        dao.create(
            UserDTO(
                role=UserRole.USER,
                login="admin",
                email="another@example.test",
                passwordHash="hash",
                birthDate=date(1990, 1, 1),
            )
        )


def test_support_dao_hydrates_support_types_and_groups_by_film(database):
    supportType = SupportTypeDAO(database).create(
        SupportTypeDTO(name="Blu-ray", mode="physical")
    )
    dao = SupportDAO(database)
    support = dao.create(
        SupportDTO(
            idFilm="film-1",
            idSupportType=supportType.idSupportType,
            location="Shelf A",
        )
    )

    hydrated = dao.getById(support.idSupport)

    assert hydrated.supportType == supportType
    assert dao.getByFilmIds(["film-1", "film-2"]) == {
        "film-1": [hydrated],
        "film-2": [],
    }
    assert dao.getFilmIdsBySupportType(supportType.idSupportType) == ["film-1"]
    assert dao.existsForFilm("film-1")
    assert dao.existsForType(supportType.idSupportType)


def test_film_dao_hydrates_references_and_combines_search_filters(database):
    database["directors"].insert_one(
        {"idDirector": 1, "lastName": "Nolan", "firstName": "Christopher"}
    )
    database["classifications"].insert_one(
        {"idClassification": 1, "minAge": 12}
    )
    database["languages"].insert_one(
        {"idLanguage": 1, "code": "en", "name": "English"}
    )
    database["genres"].insert_one({"idGenre": 1, "nameGenre": "Sci-fi"})
    database["actors"].insert_one(
        {"idActor": 1, "firstName": "Matthew", "lastName": "McConaughey"}
    )
    dao = FilmDAO(database)
    film = FilmDTO(
        title="Interstellar",
        synopsis="Space",
        releaseDate=date(2014, 11, 5),
        duration=169,
        posterUrl="https://example.test/poster.png",
        addedDate=date(2026, 1, 1),
        director=DirectorDTO(idDirector=1, lastName="Nolan", firstName="Christopher"),
        classification=ClassificationDTO(idClassification=1, minAge=12),
        nativeLanguage=LanguageDTO(idLanguage=1, code="en", name="English"),
        languages=[LanguageDTO(idLanguage=1, code="en", name="English")],
        genre=[GenreDTO(idGenre=1, nameGenre="Sci-fi")],
        actors=[ActorDTO(idActor=1, firstName="Matthew", lastName="McConaughey")],
    )

    dao.createFilm(film)
    loaded = dao.getFilmById(film.idFilm)
    filtered = dao.searchFilms(
        {"title": "inter", "genre": 1}, allowedClassificationIds=[1]
    )

    assert loaded.director.firstName == "Christopher"
    assert loaded.classification.minAge == 12
    assert loaded.languages[0].code == "en"
    assert loaded.genre[0].nameGenre == "Sci-fi"
    assert loaded.actors[0].lastName == "McConaughey"
    assert filtered == [loaded]
    assert not dao.searchFilms({}, allowedClassificationIds=[] )
    assert dao.existsFilm(film.idFilm)


def test_loan_dao_guards_one_active_loan_and_releases_support_on_return(database):
    dao = LoanDAO(database)
    now = datetime.now(timezone.utc)

    def loan(idLoan):
        return LoanDTO(
            idLoan=idLoan,
            idUser=idLoan,
            idPhysicalSupport=7,
            startDate=now,
            expectedReturnDate=now + timedelta(days=30),
        )

    dao.create(loan(1))
    assert dao.hasActiveLoanForSupport(7)
    assert dao.getActivePhysicalSupportIds() == {7}
    with pytest.raises(DuplicateKeyError):
        dao.create(loan(2))

    returnedAt = now + timedelta(days=1)
    database["loans"].update_one(
        {"idLoan": 1}, {"$set": {"actualReturnDate": returnedAt}}
    )
    assert not dao.hasActiveLoanForSupport(7)
    dao.create(loan(2))
    assert dao.getByIdAndUserId(2, 2).idLoan == 2
    assert len(dao.getByUserId(2)) == 1
    assert len(dao.getAll()) == 2
    assert dao.nextId() == 1
    assert dao.nextId() == 2


def test_loan_dao_return_uses_an_atomic_active_loan_condition():
    database = MagicMock()
    collection = Mock()
    counters = Mock()
    database.__getitem__.side_effect = lambda name: {
        "loans": collection,
        "counters": counters,
    }[name]
    dao = LoanDAO(database)
    now = datetime.now(timezone.utc)
    expected = LoanDTO(1, 2, 3, now, now + timedelta(days=30), now)
    collection.find_one_and_update.return_value = expected.toDict()

    returned = dao.markReturned(1, now)

    assert returned == expected
    collection.find_one_and_update.assert_called_once_with(
        {"idLoan": 1, "actualReturnDate": None},
        {"$set": {"actualReturnDate": now}},
        projection={"_id": 0},
        return_document=1,
    )
