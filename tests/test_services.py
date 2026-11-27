from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock

import bcrypt
import pytest
from pymongo.errors import DuplicateKeyError

from app.Exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    ConflictError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
    UserInputError,
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
from app.services.ActorService import ActorService
from app.services.AuthService import AuthService
from app.services.ClassificationServcie import ClassificationService
from app.services.DirectorService import DirectorService
from app.services.FilmService import FilmService
from app.services.GenreService import GenreService
from app.services.LanguageService import LanguageService
from app.services.LoanService import LoanService
from app.services.SupportService import SupportService
from app.services.SupportTypeService import SupportTypeService
from app.services.UserService import UserService


@pytest.mark.parametrize(
    ("serviceType", "createMethod", "inputData", "idField", "entityName"),
    [
        (ActorService, "createActor", {"firstName": "Ada", "lastName": "Lovelace"}, "idActor", "Actor"),
        (DirectorService, "createDirector", {"firstName": "Ava", "lastName": "DuVernay"}, "idDirector", "Director"),
        (GenreService, "createGenre", {"nameGenre": "Drama"}, "idGenre", "Genre"),
        (LanguageService, "createLanguage", {"code": "FR", "name": "French"}, "idLanguage", "Language"),
        (ClassificationService, "createClassification", {"minAge": 16}, "idClassification", "Classification"),
    ],
)
def test_catalog_services_create_and_translate_duplicate_keys(
    serviceType, createMethod, inputData, idField, entityName
):
    dao = Mock()
    dao.create.side_effect = lambda dto: dto
    service = serviceType(dao)
    result = getattr(service, createMethod)(inputData)

    assert getattr(result, idField) is None
    if serviceType is LanguageService:
        assert result.code == "fr"

    dao.create.side_effect = DuplicateKeyError("duplicate")
    with pytest.raises(AlreadyExistsError, match=entityName):
        getattr(service, createMethod)(inputData)


@pytest.mark.parametrize(
    ("serviceType", "methodName"),
    [
        (ActorService, "getActorById"),
        (DirectorService, "getDirectorById"),
        (GenreService, "getGenreById"),
        (LanguageService, "getLanguageById"),
        (ClassificationService, "getClassificationById"),
    ],
)
def test_catalog_services_raise_not_found(serviceType, methodName):
    repository = Mock()
    repository.getById.return_value = None
    service = serviceType(repository)
    with pytest.raises(NotFoundError):
        getattr(service, methodName)(123)


def test_catalog_update_requires_matching_path_identifier():
    cases = [
        (ActorService(Mock()), "updateActor", "idActor"),
        (DirectorService(Mock()), "updateDirector", "idDirector"),
        (GenreService(Mock()), "updateGenre", "idGenre"),
        (LanguageService(Mock()), "updateLanguage", "idLanguage"),
        (ClassificationService(Mock()), "updateClassification", "idClassification"),
    ]

    for service, methodName, idField in cases:
        with pytest.raises(InvalidRequestError):
            getattr(service, methodName)(4, {idField: 5})


@pytest.mark.parametrize(
    ("serviceType", "updateMethod", "deleteMethod", "inputData", "idField"),
    [
        (ActorService, "updateActor", "deleteActor", {"firstName": "Ada", "lastName": "Lovelace"}, "idActor"),
        (DirectorService, "updateDirector", "deleteDirector", {"firstName": "Ava", "lastName": "DuVernay"}, "idDirector"),
        (GenreService, "updateGenre", "deleteGenre", {"nameGenre": "Drama"}, "idGenre"),
        (LanguageService, "updateLanguage", "deleteLanguage", {"code": "fr", "name": "French"}, "idLanguage"),
        (ClassificationService, "updateClassification", "deleteClassification", {"minAge": 12}, "idClassification"),
    ],
)
def test_catalog_services_update_and_delete_existing_entities(
    serviceType, updateMethod, deleteMethod, inputData, idField
):
    dao = Mock()
    dao.update.return_value = True
    dao.delete.return_value = True
    service = serviceType(dao)

    updated = getattr(service, updateMethod)(8, inputData)
    getattr(service, deleteMethod)(8)

    assert getattr(updated, idField) == 8
    dao.update.assert_called_once_with(updated)
    dao.delete.assert_called_once_with(8)

    dao.update.return_value = False
    with pytest.raises(NotFoundError):
        getattr(service, updateMethod)(8, inputData)
    dao.delete.return_value = False
    with pytest.raises(NotFoundError):
        getattr(service, deleteMethod)(8)


def _new_user(idUser=10, role=UserRole.USER, birthDate=None, passwordHash=""):
    return UserDTO(
        idUser=idUser,
        role=role,
        login=f"user{idUser}",
        email=f"user{idUser}@example.test",
        passwordHash=passwordHash,
        birthDate=birthDate or date(1990, 1, 1),
    )


def test_user_creation_validates_confirmation_and_stores_a_hash():
    dao = Mock()
    dao.getByLogin.return_value = None
    dao.getByEmail.return_value = None
    dao.create.side_effect = lambda user: user
    service = UserService(dao)
    data = {
        "login": " reader ",
        "email": " reader@example.test ",
        "password": "StrongPassword1!",
        "confirmPassword": "StrongPassword1!",
        "birthDate": "1990-01-01",
    }

    user = service.createUser(data)

    assert user.login == "reader"
    assert user.email == "reader@example.test"
    assert bcrypt.checkpw(b"StrongPassword1!", user.passwordHash.encode())
    assert user.role is UserRole.USER

    with pytest.raises(UserInputError, match="identiques"):
        service.createUser({**data, "confirmPassword": "DifferentPassword2!"})


def test_user_update_rejects_role_and_mismatched_identifier():
    service = UserService(Mock())
    with pytest.raises(InvalidRequestError):
        service.updateUser(1, {"role": UserRole.ADMIN.value})
    with pytest.raises(InvalidRequestError):
        service.updateUser(1, {"idUser": 2})


def test_user_update_hashes_new_password_and_rejects_future_birth_date():
    user = _new_user()
    dao = Mock()
    dao.getById.return_value = user
    dao.getByLogin.return_value = None
    dao.getByEmail.return_value = None
    dao.update.return_value = True
    service = UserService(dao)

    updated = service.updateUser(
        user.idUser,
        {"password": "NewStrongPassword2!", "birthDate": "1991-02-03"},
    )
    assert updated.birthDate == date(1991, 2, 3)
    assert bcrypt.checkpw(
        b"NewStrongPassword2!", updated.passwordHash.encode()
    )

    futureDate = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(UserInputError, match="futur"):
        service.updateUser(user.idUser, {"birthDate": futureDate})


def test_user_role_change_validates_role_and_missing_user():
    dao = Mock()
    dao.getById.return_value = None
    service = UserService(dao)

    with pytest.raises(UserInputError, match="rôle"):
        service.updateUserRole(1, "not-a-role")
    with pytest.raises(NotFoundError):
        service.updateUserRole(1, UserRole.MANAGER.value)


def test_film_service_validates_related_entities_and_support_dependencies():
    filmDAO = Mock()
    filmDAO.createFilm.side_effect = lambda film: _set_film_id(film)
    filmDAO.updateFilm.return_value = True
    filmDAO.existsFilm.return_value = True
    filmDAO.deleteFilm.return_value = True
    supportDAO = Mock()
    supportDAO.getByFilmIds.return_value = {}
    supportDAO.existsForFilm.return_value = False
    references = Mock()
    references.exists.return_value = True
    service = FilmService(
        filmDAO,
        references,
        references,
        references,
        references,
        supportDAO,
        Mock(),
    )
    filmData = {
        "title": "Film",
        "synopsis": "Synopsis",
        "releaseDate": "2020-01-01",
        "duration": 100,
        "posterUrl": "https://example.test/poster.png",
        "addedDate": "2024-01-01",
        "director": {"idDirector": 1},
        "classification": {"idClassification": 2},
        "nativeLanguage": {"idLanguage": 3},
        "languages": [{"idLanguage": 3}],
        "genre": [{"idGenre": 4}],
        "actors": [{"idActor": 5}],
    }

    created = service.createFilm(filmData)
    updated = service.updateFilm("film-2", filmData)
    service.deleteFilm("film-2")

    assert created.idFilm == "film-1"
    assert updated.idFilm == "film-2"
    assert references.exists.call_count >= 5
    filmDAO.deleteFilm.assert_called_once_with("film-2")

    with pytest.raises(InvalidRequestError):
        service.updateFilm("film-1", {**filmData, "idFilm": "film-other"})
    references.exists.return_value = False
    with pytest.raises(InvalidReferenceError, match="Director"):
        service.createFilm(filmData)
    filmDAO.existsFilm.return_value = False
    with pytest.raises(NotFoundError):
        service.deleteFilm("missing")


def _set_film_id(film):
    film.idFilm = "film-1"
    return film


def test_authentication_verifies_password_and_reloads_user_from_token(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-jwt-secret-at-least-thirty-two-bytes"
    )
    user = _new_user(passwordHash=bcrypt.hashpw(
        b"StrongPassword1!", bcrypt.gensalt()
    ).decode())
    dao = Mock()
    dao.getByLogin.return_value = user
    dao.getById.return_value = user
    service = AuthService(dao)

    assert service.authenticate(user.login, "StrongPassword1!") is user
    token = service.generateToken(user)
    assert service.verifyToken(token) is user

    with pytest.raises(AuthenticationError):
        service.authenticate(user.login, "wrong")
    with pytest.raises(InvalidRequestError):
        service.verifyToken("invalid-token")


def test_auth_service_requires_a_configured_secret(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        AuthService(Mock())


def _film(idFilm="film-1", classification=None):
    return FilmDTO(
        idFilm=idFilm,
        title="Film",
        synopsis="Synopsis",
        releaseDate=date(2020, 1, 1),
        duration=100,
        posterUrl="https://example.test/poster.png",
        addedDate=date(2024, 1, 1),
        classification=classification,
    )


def test_film_service_applies_age_classification_and_role_rules():
    user = _new_user(
        idUser=1,
        role=UserRole.USER,
        birthDate=date.today().replace(year=date.today().year - 12),
    )
    film = _film(classification=ClassificationDTO(12, 2))
    filmDAO = Mock()
    filmDAO.getFilmById.return_value = film
    filmDAO.searchFilms.return_value = [film]
    supportDAO = Mock()
    supportDAO.getByFilmIds.return_value = {"film-1": []}
    userDAO = Mock()
    userDAO.getById.return_value = user
    classificationDAO = Mock()
    classificationDAO.getIdsAllowedForAge.return_value = [2]
    service = FilmService(
        filmDAO, Mock(), Mock(), Mock(), classificationDAO, supportDAO, userDAO
    )

    assert service.getFilmById("film-1", user.idUser) is film
    assert service.searchFilms({}, user.idUser) == [film]
    assert classificationDAO.getIdsAllowedForAge.called

    classificationDAO.getIdsAllowedForAge.return_value = [1]
    with pytest.raises(NotFoundError):
        service.getFilmById("film-1", user.idUser)

    user.role = UserRole.MANAGER
    classificationDAO.getIdsAllowedForAge.reset_mock()
    service.getFilmById("film-1", user.idUser)
    classificationDAO.getIdsAllowedForAge.assert_not_called()


def test_film_deletion_refuses_to_delete_films_with_supports():
    filmDAO = Mock()
    filmDAO.existsFilm.return_value = True
    supportDAO = Mock()
    supportDAO.existsForFilm.return_value = True
    service = FilmService(
        filmDAO, Mock(), Mock(), Mock(), Mock(), supportDAO, Mock()
    )

    with pytest.raises(ConflictError):
        service.deleteFilm("film-1")


def test_support_service_validates_physical_and_digital_supports():
    filmDAO = Mock()
    filmDAO.existsFilm.return_value = True
    physicalType = SupportTypeDTO(idSupportType=1, name="DVD", mode="physical")
    digitalType = SupportTypeDTO(idSupportType=2, name="Stream", mode="digital")
    supportTypeDAO = Mock()
    supportTypeDAO.getById.side_effect = {1: physicalType, 2: digitalType}.get
    supportDAO = Mock()
    supportDAO.create.side_effect = lambda support: support
    service = SupportService(supportDAO, filmDAO, supportTypeDAO, Mock())

    physical = service.createSupport(
        {"idFilm": "film-1", "idSupportType": 1, "location": "Shelf A"}
    )
    digital = service.createSupport(
        {"idFilm": "film-1", "idSupportType": 2, "url": "https://example.test/watch"}
    )
    assert physical.supportType is physicalType
    assert digital.supportType is digitalType

    with pytest.raises(InvalidRequestError, match="location"):
        service.createSupport({"idFilm": "film-1", "idSupportType": 1})
    with pytest.raises(InvalidRequestError, match="HTTP"):
        service.createSupport(
            {"idFilm": "film-1", "idSupportType": 2, "url": "javascript:alert(1)"}
        )


def test_support_service_reads_updates_deletes_and_translates_duplicates():
    support = SupportDTO(
        idSupport=7,
        idFilm="film-1",
        idSupportType=1,
        location="Shelf A",
    )
    supportDAO = Mock()
    supportDAO.getAll.return_value = [support]
    supportDAO.getById.return_value = support
    supportDAO.update.return_value = True
    supportDAO.delete.return_value = True
    supportDAO.create.side_effect = DuplicateKeyError("duplicate")
    filmDAO = Mock()
    filmDAO.existsFilm.return_value = True
    supportTypeDAO = Mock()
    supportTypeDAO.getById.return_value = SupportTypeDTO(
        idSupportType=1, name="DVD", mode="physical"
    )
    service = SupportService(supportDAO, filmDAO, supportTypeDAO, Mock())

    assert service.getAllSupports() == [support]
    assert service.getSupportById(7) is support
    updated = service.updateSupport(
        7, {"idFilm": "film-1", "idSupportType": 1, "location": "Shelf B"}
    )
    assert updated.idSupport == 7
    service.deleteSupport(7)
    with pytest.raises(AlreadyExistsError):
        service.createSupport(
            {"idFilm": "film-1", "idSupportType": 1, "location": "Shelf C"}
        )

    supportDAO.getById.return_value = None
    with pytest.raises(NotFoundError):
        service.getSupportById(99)
    supportDAO.delete.return_value = False
    with pytest.raises(NotFoundError):
        service.deleteSupport(99)
    supportDAO.update.return_value = False
    with pytest.raises(NotFoundError):
        service.updateSupport(
            7, {"idFilm": "film-1", "idSupportType": 1, "location": "Shelf B"}
        )


@pytest.mark.parametrize(
    ("filmExists", "supportType", "supportData", "error"),
    [
        (
            False,
            SupportTypeDTO(idSupportType=1, name="DVD", mode="physical"),
            {"location": "A"},
            InvalidReferenceError,
        ),
        (True, None, {"location": "A"}, InvalidReferenceError),
        (
            True,
            SupportTypeDTO(idSupportType=1, name="DVD", mode="physical"),
            {"location": "A", "url": "https://example.test"},
            InvalidRequestError,
        ),
        (
            True,
            SupportTypeDTO(idSupportType=1, name="Stream", mode="digital"),
            {"url": "https://example.test", "location": "A"},
            InvalidRequestError,
        ),
        (
            True,
            SupportTypeDTO(idSupportType=1, name="Other", mode="unknown"),
            {"location": "A"},
            InvalidRequestError,
        ),
    ],
)
def test_support_service_rejects_invalid_references_and_mode_fields(
    filmExists, supportType, supportData, error
):
    filmDAO = Mock()
    filmDAO.existsFilm.return_value = filmExists
    supportTypeDAO = Mock()
    supportTypeDAO.getById.return_value = supportType
    service = SupportService(Mock(), filmDAO, supportTypeDAO, Mock())
    with pytest.raises(error):
        service.createSupport(
            {"idFilm": "film-1", "idSupportType": 1, **supportData}
        )


def test_support_availability_is_computed_only_for_physical_supports():
    loanDAO = Mock()
    loanDAO.getActivePhysicalSupportIds.return_value = {1}
    service = SupportService(Mock(), Mock(), Mock(), loanDAO)
    physical = SupportDTO(
        idSupport=1,
        idFilm="film-1",
        idSupportType=1,
        location="Shelf A",
        supportType=SupportTypeDTO(
            idSupportType=1, name="DVD", mode="physical"
        ),
    )
    digital = SupportDTO(
        idSupport=2,
        idFilm="film-2",
        idSupportType=2,
        url="https://example.test/watch",
        supportType=SupportTypeDTO(
            idSupportType=2, name="Stream", mode="digital"
        ),
    )

    data = service.toPublicDicts([physical, digital])
    assert data[0]["isAvailable"] is False
    assert data[1]["isAvailable"] is None


def test_support_type_cannot_change_mode_while_in_use():
    supportTypeDAO = Mock()
    supportTypeDAO.getById.return_value = SupportTypeDTO(1, "DVD", "physical")
    supportDAO = Mock()
    supportDAO.existsForType.return_value = True
    service = SupportTypeService(supportTypeDAO, supportDAO)

    with pytest.raises(ConflictError):
        service.updateSupportType(
            1, {"name": "Streaming", "mode": "digital"}
        )


def test_support_type_service_crud_and_validation():
    supportType = SupportTypeDTO(
        idSupportType=1, name="DVD", mode="physical"
    )
    supportTypeDAO = Mock()
    supportTypeDAO.getAll.return_value = [supportType]
    supportTypeDAO.getById.return_value = supportType
    supportTypeDAO.create.side_effect = lambda value: value
    supportTypeDAO.update.return_value = True
    supportTypeDAO.delete.return_value = True
    supportDAO = Mock()
    supportDAO.existsForType.return_value = False
    service = SupportTypeService(supportTypeDAO, supportDAO)

    assert service.getAllSupportTypes() == [supportType]
    assert service.getSupportTypeById(1) is supportType
    created = service.createSupportType({"name": "Blu-ray", "mode": "physical"})
    assert created.idSupportType is None
    updated = service.updateSupportType(
        1, {"name": "Disc", "mode": "physical"}
    )
    assert updated.name == "Disc"
    service.deleteSupportType(1)

    with pytest.raises(InvalidRequestError, match="mode"):
        service.createSupportType({"name": "Invalid", "mode": "streaming"})

    supportTypeDAO.getById.return_value = None
    with pytest.raises(NotFoundError):
        service.getSupportTypeById(99)


def test_loan_service_enforces_physical_support_and_atomic_duplicate_failure():
    loanDAO = Mock()
    loanDAO.nextId.return_value = 10
    loanDAO.hasActiveLoanForSupport.return_value = False
    loanDAO.create.side_effect = lambda loan: loan
    userDAO = Mock()
    userDAO.exists.return_value = True
    support = SupportDTO(
        idSupport=7,
        idFilm="film-1",
        idSupportType=1,
        location="Shelf A",
        supportType=SupportTypeDTO(
            idSupportType=1, name="DVD", mode="physical"
        ),
    )
    supportDAO = Mock()
    supportDAO.getById.return_value = support
    filmService = Mock()
    service = LoanService(loanDAO, userDAO, supportDAO, filmService)

    loan = service.borrow(3, {"idPhysicalSupport": 7})
    assert loan.idLoan == 10
    assert loan.idUser == 3
    assert loan.startDate.tzinfo == timezone.utc
    assert loan.expectedReturnDate - loan.startDate == timedelta(days=30)
    filmService.getFilmForUser.assert_called_once_with("film-1", 3)

    loanDAO.create.side_effect = DuplicateKeyError("active loan index")
    with pytest.raises(ConflictError):
        service.borrow(4, {"idPhysicalSupport": 7})

    support.supportType.mode = "digital"
    with pytest.raises(InvalidReferenceError):
        service.borrow(3, {"idPhysicalSupport": 7})


def test_loan_return_distinguishes_missing_and_already_returned():
    dao = Mock()
    dao.markReturned.return_value = None
    dao.getById.return_value = None
    service = LoanService(dao, Mock(), Mock(), Mock())

    with pytest.raises(NotFoundError):
        service.returnLoan(9)

    dao.getById.return_value = Mock()
    with pytest.raises(ConflictError):
        service.returnLoan(9)
