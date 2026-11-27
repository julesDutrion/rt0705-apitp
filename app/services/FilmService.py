
from datetime import date
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError

from ..dao import (
    ClassificationDAO,
    DirectorDAO,
    FilmDAO,
    GenreDAO,
    LanguageDAO,
    SupportDAO,
    UserDAO,
)
from ..Exceptions import (
    AlreadyExistsError,
    ConflictError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
)
from ..models import FilmDTO, UserDTO, UserRole
from ._input import dtoFromInput


class FilmService:
    def __init__(
        self,
        filmDAO: FilmDAO,
        directorDAO: DirectorDAO,
        genreDAO: GenreDAO,
        languageDAO: LanguageDAO,
        classificationDAO: ClassificationDAO,
        supportDAO: SupportDAO,
        userDAO: UserDAO,
    ) -> None:
        self._filmDAO = filmDAO
        self._directorDAO = directorDAO
        self._genreDAO = genreDAO
        self._languageDAO = languageDAO
        self._classificationDAO = classificationDAO
        self._supportDAO = supportDAO
        self._userDAO = userDAO

    # ------------------------------------------------------------------ #
    # Lecture
    # ------------------------------------------------------------------ #
    def getAllFilms(self, idUser: Optional[int] = None) -> List[FilmDTO]:
        return self.getFilmsForUser(idUser, {})

    def searchFilms(
        self,
        filters: Dict[str, Any],
        idUser: Optional[int] = None,
    ) -> List[FilmDTO]:
        return self.getFilmsForUser(idUser, filters)

    def getFilmsForUser(
        self,
        idUser: Optional[int],
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[FilmDTO]:
        allowedClassificationIds = self._getAllowedClassificationIds(idUser)
        return self._searchFilms(filters or {}, allowedClassificationIds)

    def _searchFilms(
        self,
        filters: Dict[str, Any],
        allowedClassificationIds: Optional[List[int]],
    ) -> List[FilmDTO]:
        """
        Recherche des films selon plusieurs critères cumulables.

        allowedClassificationIds :
            None = aucune restriction.
            [] = aucune classification autorisée.
            [1, 2] = classifications autorisées.

        supportType :
            Identifiant du type de support; seuls les films ayant un support
            associé à ce type sont retournés.
        """
        supportFilmIds = None
        supportTypeId = filters.get("supportType")
        if supportTypeId is not None:
            supportFilmIds = self._supportDAO.getFilmIdsBySupportType(
                supportTypeId
            )

        films = self._filmDAO.searchFilms(
            filters,
            allowedClassificationIds,
            supportFilmIds,
        )
        return self._attachSupports(films)

    def getFilmById(
        self,
        idFilm: str,
        idUser: Optional[int] = None,
    ) -> FilmDTO:
        allowedClassificationIds = self._getAllowedClassificationIds(idUser)
        film = self._filmDAO.getFilmById(idFilm)

        if film is None:
            raise NotFoundError(f"Film {idFilm} not found")

        # Vérifie que le film est autorisé pour le compte.
        if (
            allowedClassificationIds is not None
            and (
                film.classification is None
                or type(film.classification.idClassification) is not int
                or film.classification.idClassification
                not in allowedClassificationIds
            )
        ):
            raise NotFoundError(f"Film {idFilm} not found")

        return self._attachSupports([film])[0]

    def getFilmForUser(self, idFilm: str, idUser: int) -> FilmDTO:
        return self.getFilmById(idFilm, idUser)

    def calculateUserAge(self, user: UserDTO) -> int:
        if type(user.birthDate) is not date or user.birthDate > date.today():
            raise InvalidReferenceError(
                f"User {user.idUser} has an invalid birth date"
            )
        return user.calculateAge()

    def _getAllowedClassificationIds(
        self, idUser: Optional[int]
    ) -> Optional[List[int]]:
        if idUser is None:
            return None
        try:
            user = self._userDAO.getById(idUser)
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidReferenceError(
                f"User {idUser} has invalid account data"
            ) from error
        if user is None:
            raise NotFoundError(f"User {idUser} not found")

        if user.role in {UserRole.MANAGER, UserRole.ADMIN}:
            return None
        if user.role != UserRole.USER:
            raise InvalidReferenceError(f"User {idUser} has an invalid role")

        age = self.calculateUserAge(user)
        return self._classificationDAO.getIdsAllowedForAge(age)

    # ------------------------------------------------------------------ #
    # Écriture
    # ------------------------------------------------------------------ #
    def createFilm(self, data: Any) -> FilmDTO:
        film = dtoFromInput(data, FilmDTO.fromDictWithoutId)
        self._checkReferences(film)

        try:
            createdFilm = self._filmDAO.createFilm(film)
            return self._attachSupports([createdFilm])[0]
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Film {film.idFilm} already exists")

    def updateFilm(self, idFilm: str, data: Any) -> FilmDTO:
        if (
            isinstance(data, dict)
            and "idFilm" in data
            and data["idFilm"] != idFilm
        ):
            raise InvalidRequestError(
                "idFilm in the URL and in the body must match"
            )
        film = dtoFromInput(data, FilmDTO.fromDictWithoutId)
        film.idFilm = idFilm
        self._checkReferences(film)

        if not self._filmDAO.updateFilm(film):
            raise NotFoundError(f"Film {film.idFilm} not found")

        return self._attachSupports([film])[0]

    def deleteFilm(self, idFilm: str) -> None:
        if not self._filmDAO.existsFilm(idFilm):
            raise NotFoundError(f"Film {idFilm} not found")
        if self._supportDAO.existsForFilm(idFilm):
            raise ConflictError(f"Film {idFilm} still has associated supports")
        if not self._filmDAO.deleteFilm(idFilm):
            raise NotFoundError(f"Film {idFilm} not found")

    def _attachSupports(self, films: List[FilmDTO]) -> List[FilmDTO]:
        supportsByFilm = self._supportDAO.getByFilmIds(
            film.idFilm for film in films if film.idFilm is not None
        )
        for film in films:
            if film.idFilm is not None:
                film.supports = supportsByFilm.get(film.idFilm, [])
        return films

    # ------------------------------------------------------------------ #
    # Interne : vérifie que les entités liées existent
    # ------------------------------------------------------------------ #
    def _checkReferences(self, film: FilmDTO) -> None:
        if film.director and not self._directorDAO.exists(film.director.idDirector):
            raise InvalidReferenceError(
                f"Director {film.director.idDirector} does not exist"
            )

        if film.classification and not self._classificationDAO.exists(
            film.classification.idClassification
        ):
            raise InvalidReferenceError(
                f"Classification {film.classification.idClassification} does not exist"
            )

        if film.nativeLanguage and not self._languageDAO.exists(
            film.nativeLanguage.idLanguage
        ):
            raise InvalidReferenceError(
                f"Language {film.nativeLanguage.idLanguage} does not exist"
            )

        for language in film.languages:
            if not self._languageDAO.exists(language.idLanguage):
                raise InvalidReferenceError(
                    f"Language {language.idLanguage} does not exist"
                )

        for genre in film.genre:
            if not self._genreDAO.exists(genre.idGenre):
                raise InvalidReferenceError(
                    f"Genre {genre.idGenre} does not exist"
                )
