
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError

from ..dao import (
    ClassificationDAO,
    DirectorDAO,
    FilmDAO,
    GenreDAO,
    LanguageDAO,
    SupportDAO,
)
from ..Exceptions import (
    AlreadyExistsError,
    ConflictError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
)
from ..models import FilmDTO
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
    ) -> None:
        self._filmDAO = filmDAO
        self._directorDAO = directorDAO
        self._genreDAO = genreDAO
        self._languageDAO = languageDAO
        self._classificationDAO = classificationDAO
        self._supportDAO = supportDAO

    # ------------------------------------------------------------------ #
    # Lecture
    # ------------------------------------------------------------------ #
    def getAllFilms(self) -> List[FilmDTO]:
        return self.searchFilms({})

    def searchFilms(
        self,
        filters: Dict[str, Any],
        allowedClassificationIds: Optional[List[int]] = None
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
        allowedClassificationIds: Optional[List[int]] = None
    ) -> FilmDTO:
        film = self._filmDAO.getFilmById(idFilm)

        if film is None:
            raise NotFoundError(f"Film {idFilm} not found")

        # Vérifie que le film est autorisé pour le compte.
        if (
            allowedClassificationIds is not None
            and (
                film.classification is None
                or film.classification.idClassification not in allowedClassificationIds
            )
        ):
            raise NotFoundError(f"Film {idFilm} not found")

        return self._attachSupports([film])[0]

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
