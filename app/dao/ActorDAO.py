import re
from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import ActorDTO

_NO_MONGO_ID = {"_id": 0}


class ActorDAO:
    COLLECTION_NAME = "actors"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idActor", ASCENDING)], unique=True)

    def getAll(self) -> List[ActorDTO]:
        return self._find({})

    def getById(self, idActor: int) -> Optional[ActorDTO]:
        document = self._collection.find_one({"idActor": idActor}, _NO_MONGO_ID)
        return ActorDTO.fromDict(document) if document else None

    def exists(self, idActor: int) -> bool:
        return self._collection.count_documents({"idActor": idActor}, limit=1) > 0

    def searchByName(self, name: str) -> List[ActorDTO]:
        pattern = {"$regex": re.escape(name), "$options": "i"}
        return self._find({"$or": [{"firstName": pattern}, {"lastName": pattern}]})

    def create(self, actor: ActorDTO) -> ActorDTO:
        if actor.idActor is None:
            document = self._collection.find_one(
                {}, {"idActor": 1, "_id": 0}, sort=[("idActor", DESCENDING)]
            )
            nextId = (document["idActor"] + 1) if document else 1
            while self.exists(nextId):
                nextId += 1
            actor.idActor = nextId
        self._collection.insert_one(actor.toDict())
        return actor

    def update(self, actor: ActorDTO) -> bool:
        result = self._collection.replace_one(
            {"idActor": actor.idActor}, actor.toDict()
        )
        return result.matched_count == 1

    def delete(self, idActor: int) -> bool:
        result = self._collection.delete_one({"idActor": idActor})
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[ActorDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort(
            "idActor", ASCENDING
        )
        return [ActorDTO.fromDict(document) for document in documents]
