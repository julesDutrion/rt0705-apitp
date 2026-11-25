from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import ActorDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import ActorDTO
from ._input import dtoFromInput


class ActorService:
    def __init__(self, actorDAO: ActorDAO) -> None:
        self._actorDAO = actorDAO

    def getAllActors(self) -> List[ActorDTO]:
        return self._actorDAO.getAll()

    def searchActorsByName(self, name: str) -> List[ActorDTO]:
        return self._actorDAO.searchByName(name)

    def getActorById(self, idActor: int) -> ActorDTO:
        actor = self._actorDAO.getById(idActor)
        if actor is None:
            raise NotFoundError(f"Actor {idActor} not found")
        return actor

    def createActor(self, data: Any) -> ActorDTO:
        actor = dtoFromInput(data, ActorDTO.fromDictWithoutId)
        try:
            return self._actorDAO.create(actor)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Actor {actor.idActor} already exists")

    def updateActor(self, idActor: int, data: Any) -> ActorDTO:
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
        if not self._actorDAO.delete(idActor):
            raise NotFoundError(f"Actor {idActor} not found")
