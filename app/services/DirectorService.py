from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import DirectorDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import DirectorDTO
from ._input import dtoFromInput


class DirectorService:
    """Classe qui représente le service de gestion des réalisateurs."""

    def __init__(self, directorDAO: DirectorDAO) -> None:
        self._directorDAO = directorDAO

    def getAllDirectors(self) -> List[DirectorDTO]:
        """
        Méthode qui récupère tous les réalisateurs.

        :return: Liste des DTO de réalisateurs.
        """
        return self._directorDAO.getAll()

    def searchDirectorsByName(self, name: str) -> List[DirectorDTO]:
        """
        Méthode qui recherche les réalisateurs par nom ou prénom.

        :param name: Texte recherché.
        :return: Liste des réalisateurs correspondants.
        """
        return self._directorDAO.searchByName(name)

    def getDirectorById(self, idDirector: int) -> DirectorDTO:
        """
        Méthode qui récupère un réalisateur par son identifiant.

        :param idDirector: Identifiant du réalisateur.
        :return: DTO du réalisateur.
        :raises NotFoundError: Si le réalisateur n'existe pas.
        """
        director = self._directorDAO.getById(idDirector)
        if director is None:
            raise NotFoundError(f"Director {idDirector} not found")
        return director

    def createDirector(self, data: Any) -> DirectorDTO:
        """
        Méthode qui crée un réalisateur.

        :param data: Données du réalisateur.
        :return: DTO du réalisateur créé.
        :raises InvalidRequestError: Si les données sont invalides.
        :raises AlreadyExistsError: Si l'identifiant existe déjà.
        """
        director = dtoFromInput(data, DirectorDTO.fromDictWithoutId)
        try:
            return self._directorDAO.create(director)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Director {director.idDirector} already exists")

    def updateDirector(self, idDirector: int, data: Any) -> DirectorDTO:
        """
        Méthode qui remplace les données d'un réalisateur.

        :param idDirector: Identifiant du réalisateur à modifier.
        :param data: Nouvelles données du réalisateur.
        :return: DTO du réalisateur modifié.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises NotFoundError: Si le réalisateur n'existe pas.
        """
        if (
            isinstance(data, dict)
            and "idDirector" in data
            and data["idDirector"] != idDirector
        ):
            raise InvalidRequestError(
                "idDirector in the URL and in the body must match"
            )
        director = dtoFromInput(data, DirectorDTO.fromDictWithoutId)
        director.idDirector = idDirector
        if not self._directorDAO.update(director):
            raise NotFoundError(f"Director {director.idDirector} not found")
        return director

    def deleteDirector(self, idDirector: int) -> None:
        """
        Méthode qui supprime un réalisateur.

        :param idDirector: Identifiant du réalisateur à supprimer.
        :raises NotFoundError: Si le réalisateur n'existe pas.
        """
        if not self._directorDAO.delete(idDirector):
            raise NotFoundError(f"Director {idDirector} not found")