from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import GenreDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import GenreDTO
from ._input import dtoFromInput


class GenreService:
    """Classe qui représente le service de gestion des genres."""

    def __init__(self, genreDAO: GenreDAO) -> None:
        self._genreDAO = genreDAO

    def getAllGenres(self) -> List[GenreDTO]:
        """
        Méthode qui récupère tous les genres.

        :return: Liste des DTO de genres.
        """
        return self._genreDAO.getAll()

    def searchGenresByName(self, name: str) -> List[GenreDTO]:
        """
        Méthode qui recherche les genres par nom.

        :param name: Texte recherché.
        :return: Liste des genres correspondants.
        """
        return self._genreDAO.searchByName(name)

    def getGenreById(self, idGenre: int) -> GenreDTO:
        """
        Méthode qui récupère un genre par son identifiant.

        :param idGenre: Identifiant du genre.
        :return: DTO du genre.
        :raises NotFoundError: Si le genre n'existe pas.
        """
        genre = self._genreDAO.getById(idGenre)
        if genre is None:
            raise NotFoundError(f"Genre {idGenre} not found")
        return genre

    def createGenre(self, data: Any) -> GenreDTO:
        """
        Méthode qui crée un genre.

        :param data: Données du genre.
        :return: DTO du genre créé.
        :raises InvalidRequestError: Si les données sont invalides.
        :raises AlreadyExistsError: Si l'identifiant existe déjà.
        """
        genre = dtoFromInput(data, GenreDTO.fromDictWithoutId)
        try:
            return self._genreDAO.create(genre)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Genre {genre.idGenre} already exists")

    def updateGenre(self, idGenre: int, data: Any) -> GenreDTO:
        """
        Méthode qui remplace les données d'un genre.

        :param idGenre: Identifiant du genre à modifier.
        :param data: Nouvelles données du genre.
        :return: DTO du genre modifié.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises NotFoundError: Si le genre n'existe pas.
        """
        if (
            isinstance(data, dict)
            and "idGenre" in data
            and data["idGenre"] != idGenre
        ):
            raise InvalidRequestError(
                "idGenre in the URL and in the body must match"
            )
        genre = dtoFromInput(data, GenreDTO.fromDictWithoutId)
        genre.idGenre = idGenre
        if not self._genreDAO.update(genre):
            raise NotFoundError(f"Genre {genre.idGenre} not found")
        return genre

    def deleteGenre(self, idGenre: int) -> None:
        """
        Méthode qui supprime un genre.

        :param idGenre: Identifiant du genre à supprimer.
        :raises NotFoundError: Si le genre n'existe pas.
        """
        if not self._genreDAO.delete(idGenre):
            raise NotFoundError(f"Genre {idGenre} not found")