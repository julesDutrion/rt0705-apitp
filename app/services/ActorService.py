from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import ActorDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import ActorDTO
from ._input import dtoFromInput


class ActorService:
    """Classe qui représente le service de gestion des acteurs."""

    def __init__(self, actorDAO: ActorDAO) -> None:
        self._actorDAO = actorDAO

    def getAllActors(self) -> List[ActorDTO]:
        """
        Méthode qui récupère tous les acteurs.

        :return: Liste des DTO d'acteurs.
        """
        return self._actorDAO.getAll()

    def searchActorsByName(self, name: str) -> List[ActorDTO]:
        """
        Méthode qui recherche les acteurs par prénom ou nom.

        :param name: Texte recherché.
        :return: Liste des acteurs correspondants.
        """
        return self._actorDAO.searchByName(name)

    def getActorById(self, idActor: int) -> ActorDTO:
        """
        Méthode qui récupère un acteur par son identifiant.

        :param idActor: Identifiant de l'acteur.
        :return: DTO de l'acteur.
        :raises NotFoundError: Si l'acteur n'existe pas.
        """
        actor = self._actorDAO.getById(idActor)
        if actor is None:
            raise NotFoundError(f"Actor {idActor} not found")
        return actor

    def createActor(self, data: Any) -> ActorDTO:
        """
        Méthode qui crée un acteur.

        :param data: Données de l'acteur.
        :return: DTO de l'acteur créé.
        :raises InvalidRequestError: Si les données sont invalides.
        :raises AlreadyExistsError: Si l'identifiant existe déjà.
        """
        actor = dtoFromInput(data, ActorDTO.fromDictWithoutId)
        try:
            return self._actorDAO.create(actor)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Actor {actor.idActor} already exists")

    def updateActor(self, idActor: int, data: Any) -> ActorDTO:
        """
        Méthode qui remplace les données d'un acteur.

        :param idActor: Identifiant de l'acteur à modifier.
        :param data: Nouvelles données de l'acteur.
        :return: DTO de l'acteur modifié.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises NotFoundError: Si l'acteur n'existe pas.
        """
        if (
            isinstance(data, dict)
            and "idActor" in data
            and data["idActor"] != idActor
        ):
            raise InvalidRequestError(
                "idActor in the URL and in the body must match"
            )
        actor = dtoFromInput(data, ActorDTO.fromDictWithoutId)
        actor.idActor = idActor
        if not self._actorDAO.update(actor):
            raise NotFoundError(f"Actor {actor.idActor} not found")
        return actor

    def deleteActor(self, idActor: int) -> None:
        """
        Méthode qui supprime un acteur.

        :param idActor: Identifiant de l'acteur à supprimer.
        :raises NotFoundError: Si l'acteur n'existe pas.
        """
        if not self._actorDAO.delete(idActor):
            raise NotFoundError(f"Actor {idActor} not found")
