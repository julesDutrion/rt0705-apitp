from datetime import date, datetime, timedelta, timezone

from app.models import (
    ActorDTO,
    ClassificationDTO,
    FilmDTO,
    LoanDTO,
    LoanStatus,
    UserDTO,
    UserRole,
)


def test_base_dto_serializes_nested_dtos_dates_and_identifier_exclusion():
    film = FilmDTO(
        idFilm="film-1",
        title="Example",
        synopsis="Synopsis",
        releaseDate=date(2020, 1, 2),
        duration=100,
        posterUrl="https://example.test/poster.png",
        addedDate=date(2024, 2, 3),
        classification=ClassificationDTO(idClassification=3, minAge=16),
        actors=[ActorDTO(idActor=8, firstName="Ada", lastName="Lovelace")],
    )

    result = film.toDict()

    assert result["releaseDate"] == "2020-01-02"
    assert result["classification"] == {"minAge": 16, "idClassification": 3}
    assert result["actors"][0]["idActor"] == 8
    assert "idFilm" not in film.toDictWithoutId()


def test_user_public_serialization_never_exposes_password_hash():
    user = UserDTO(
        idUser=1,
        role=UserRole.USER,
        login="reader",
        email="reader@example.test",
        passwordHash="private-hash",
        birthDate=date(1990, 1, 1),
    )

    public = user.toPublicDict()

    assert "passwordHash" not in public
    assert public["role"] == UserRole.USER.value
    assert isinstance(public["age"], int)


def test_loan_normalizes_dates_and_calculates_all_statuses():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    loan = LoanDTO(
        idLoan=1,
        idUser=2,
        idPhysicalSupport=3,
        startDate=datetime(2025, 12, 1),
        expectedReturnDate=now,
    )
    overdue = LoanDTO(
        idLoan=2,
        idUser=2,
        idPhysicalSupport=4,
        startDate=now - timedelta(days=40),
        expectedReturnDate=now - timedelta(seconds=1),
    )
    returned = LoanDTO(
        idLoan=3,
        idUser=2,
        idPhysicalSupport=5,
        startDate=now - timedelta(days=3),
        expectedReturnDate=now + timedelta(days=27),
        actualReturnDate=now,
    )

    assert loan.startDate.tzinfo == timezone.utc
    assert loan.getStatus(now) is LoanStatus.IN_PROGRESS
    assert overdue.getStatus(now) is LoanStatus.OVERDUE
    assert returned.getStatus(now) is LoanStatus.RETURNED
    assert returned.toPublicDict()["statusLabel"] == "Retourné"


def test_loan_from_dict_parses_iso_dates_and_missing_return_date():
    loan = LoanDTO.fromDict(
        {
            "idLoan": 1,
            "idUser": 2,
            "idPhysicalSupport": 3,
            "startDate": "2026-01-01T10:00:00+02:00",
            "expectedReturnDate": "2026-01-31T08:00:00Z",
            "actualReturnDate": None,
        }
    )

    assert loan.startDate == datetime(2026, 1, 1, 8, tzinfo=timezone.utc)
    assert loan.expectedReturnDate == datetime(2026, 1, 31, 8, tzinfo=timezone.utc)
    assert loan.actualReturnDate is None
