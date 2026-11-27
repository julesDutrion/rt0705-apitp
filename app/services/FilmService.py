
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
    """Classe qui représente le service de gestion des films."""

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
        """
        Méthode qui récupère les films accessibles à un utilisateur.

        :param idUser: Identifiant facultatif de l'utilisateur authentifié.
        :return: Liste des DTO de films accessibles.
        :raises InvalidReferenceError: Si les données du compte sont invalides.
        :raises NotFoundError: Si l'utilisateur n'existe pas.
        """
        return self.getFilmsForUser(idUser, {})

    def searchFilms(
        self,
        filters: Dict[str, Any],
        idUser: Optional[int] = None,
    ) -> List[FilmDTO]:
        """
        Méthode qui recherche les films accessibles selon des critères.

        :param filters: Critères de recherche.
        :param idUser: Identifiant facultatif de l'utilisateur authentifié.
        :return: Liste des DTO de films correspondants.
        :raises InvalidReferenceError: Si les données du compte sont invalides.
        :raises NotFoundError: Si l'utilisateur n'existe pas.
        """
        return self.getFilmsForUser(idUser, filters)

    def getFilmsForUser(
        self,
        idUser: Optional[int],
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[FilmDTO]:
        """
        Méthode qui filtre les films selon l'utilisateur et les critères fournis.

        :param idUser: Identifiant facultatif de l'utilisateur.
        :param filters: Critères de recherche facultatifs.
        :return: Liste des DTO de films accessibles.
        :raises InvalidReferenceError: Si les données du compte sont invalides.
        :raises NotFoundError: Si l'utilisateur n'existe pas.
        """
        allowedClassificationIds = self._getAllowedClassificationIds(idUser)
        return self._searchFilms(filters or {}, allowedClassificationIds)

    def _searchFilms(
        self,
        filters: Dict[str, Any],
        allowedClassificationIds: Optional[List[int]],
    ) -> List[FilmDTO]:
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
        """
        Méthode qui récupère un film accessible par son identifiant.

        :param idFilm: Identifiant du film.
        :param idUser: Identifiant facultatif de l'utilisateur authentifié.
        :return: DTO du film accessible.
        :raises NotFoundError: Si le film n'existe pas ou n'est pas accessible.
        :raises InvalidReferenceError: Si les données du compte sont invalides.
        """
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
        """
        Méthode qui récupère un film accessible pour un utilisateur donné.

        :param idFilm: Identifiant du film.
        :param idUser: Identifiant de l'utilisateur.
        :return: DTO du film accessible.
        :raises NotFoundError: Si le film n'existe pas ou n'est pas accessible.
        :raises InvalidReferenceError: Si les données du compte sont invalides.
        """
        return self.getFilmById(idFilm, idUser)

    def calculateUserAge(self, user: UserDTO) -> int:
        """
        Méthode qui calcule et valide l'âge d'un utilisateur.

        :param user: DTO de l'utilisateur.
        :return: Âge de l'utilisateur en années.
        :raises InvalidReferenceError: Si la date de naissance est invalide.
        """
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
        """
        Méthode qui crée un film après validation de ses références.

        :param data: Données du film.
        :return: DTO du film créé.
        :raises InvalidRequestError: Si les données du film sont invalides.
        :raises InvalidReferenceError: Si une référence est absente.
        :raises AlreadyExistsError: Si l'identifiant du film existe déjà.
        """
        film = dtoFromInput(data, FilmDTO.fromDictWithoutId)
        self._checkReferences(film)

        try:
            createdFilm = self._filmDAO.createFilm(film)
            return self._attachSupports([createdFilm])[0]
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Film {film.idFilm} already exists")

    def updateFilm(self, idFilm: str, data: Any) -> FilmDTO:
        """
        Méthode qui remplace les données d'un film.

        :param idFilm: Identifiant du film à modifier.
        :param data: Nouvelles données du film.
        :return: DTO du film modifié.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises InvalidReferenceError: Si une référence est absente.
        :raises NotFoundError: Si le film n'existe pas.
        """
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
        """
        Méthode qui supprime un film sans support associé.

        :param idFilm: Identifiant du film à supprimer.
        :raises NotFoundError: Si le film n'existe pas.
        :raises ConflictError: Si des supports sont associés au film.
        """
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
