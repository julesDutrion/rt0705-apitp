from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import UserDTO

_NO_MONGO_ID = {"_id": 0}


class UserDAO:
    COLLECTION_NAME = "users"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idUser", ASCENDING)], unique=True)
        self._collection.create_index([("login", ASCENDING)], unique=True)
        self._collection.create_index([("email", ASCENDING)], unique=True)

    def getAll(self) -> List[UserDTO]:
        return self._find({})

    def getById(self, idUser: int) -> Optional[UserDTO]:
        document = self._collection.find_one({"idUser": idUser}, _NO_MONGO_ID)
        return UserDTO.fromDict(document) if document else None

    def exists(self, idUser: int) -> bool:
        return self._collection.count_documents({"idUser": idUser}, limit=1) > 0

    def getByLogin(self, login: str) -> Optional[UserDTO]:
        document = self._collection.find_one(
            {"login": login}, _NO_MONGO_ID
        )
        return UserDTO.fromDict(document) if document else None

    def getByEmail(self, email: str) -> Optional[UserDTO]:
        document = self._collection.find_one(
            {"email": email}, _NO_MONGO_ID
        )
        return UserDTO.fromDict(document) if document else None

    def create(self, user: UserDTO) -> UserDTO:
        if user.idUser is None:
            document = self._collection.find_one(
                {}, {"idUser": 1, "_id": 0}, sort=[("idUser", DESCENDING)]
            )
            nextId = (document["idUser"] + 1) if document else 1

            while self.exists(nextId):
                nextId += 1

            user.idUser = nextId

        self._collection.insert_one(user.toDict())
        return user

    def update(self, user: UserDTO) -> bool:
        result = self._collection.replace_one(
            {"idUser": user.idUser}, user.toDict()
        )
        return result.matched_count == 1

    def delete(self, idUser: int) -> bool:
        result = self._collection.delete_one({"idUser": idUser})
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[UserDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort(
            "idUser", ASCENDING
        )
        return [UserDTO.fromDict(document) for document in documents]