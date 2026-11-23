from typing import List

from pymongo.errors import DuplicateKeyError

from ..dao import ActorDAO
from ..Exceptions import AlreadyExistsError, NotFoundError
from ..models import ActorDTO


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

    def createActor(self, actor: ActorDTO) -> ActorDTO:
        try:
            return self._actorDAO.create(actor)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Actor {actor.idActor} already exists")

    def updateActor(self, actor: ActorDTO) -> ActorDTO:
        if not self._actorDAO.update(actor):
            raise NotFoundError(f"Actor {actor.idActor} not found")
        return actor

    def deleteActor(self, idActor: int) -> None:
        if not self._actorDAO.delete(idActor):
            raise NotFoundError(f"Actor {idActor} not found")
