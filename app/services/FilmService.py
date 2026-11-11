
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError

from ..dao import ClassificationDAO, DirectorDAO, FilmDAO, GenreDAO, LanguageDAO
from ..Exceptions import AlreadyExistsError, InvalidReferenceError, NotFoundError
from ..models.FilmDTO import FilmDTO


class FilmService:
    def __init__(
        self,
        filmDAO: FilmDAO,
        directorDAO: DirectorDAO,
        genreDAO: GenreDAO,
        languageDAO: LanguageDAO,
        classificationDAO: ClassificationDAO,
    ) -> None:
        self._filmDAO = filmDAO
        self._directorDAO = directorDAO
        self._genreDAO = genreDAO
        self._languageDAO = languageDAO
        self._classificationDAO = classificationDAO

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
        """
        return self._filmDAO.searchFilms(
            filters,
            allowedClassificationIds
        )

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

        return film

    # ------------------------------------------------------------------ #
    # Écriture
    # ------------------------------------------------------------------ #
    def createFilm(self, film: FilmDTO) -> FilmDTO:
        self._checkReferences(film)

        try:
            return self._filmDAO.createFilm(film)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Film {film.idFilm} already exists")

    def updateFilm(self, film: FilmDTO) -> FilmDTO:
        self._checkReferences(film)

        if not self._filmDAO.updateFilm(film):
            raise NotFoundError(f"Film {film.idFilm} not found")

        return film

    def deleteFilm(self, idFilm: str) -> None:
        if not self._filmDAO.deleteFilm(idFilm):
            raise NotFoundError(f"Film {idFilm} not found")

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
