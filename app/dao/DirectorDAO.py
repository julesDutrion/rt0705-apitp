import re
from typing import List, Optional

from pymongo import ASCENDING
from pymongo.database import Database

from ..models.DirectorDTO import DirectorDTO

_NO_MONGO_ID = {"_id": 0}

'''
    Classe représentant un DAO pour les réalisateurs
'''
class DirectorDAO:
    COLLECTION_NAME = "directors"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idDirector", ASCENDING)], unique=True)

    def getAll(self) -> List[DirectorDTO]:
        return self._find({})

    def getById(self, idDirector: int) -> Optional[DirectorDTO]:
        document = self._collection.find_one({"idDirector": idDirector}, _NO_MONGO_ID)
        return DirectorDTO.fromDict(document) if document else None

    def exists(self, idDirector: int) -> bool:
        return self._collection.count_documents({"idDirector": idDirector}, limit=1) > 0

    def searchByName(self, name: str) -> List[DirectorDTO]:
        """Recherche partielle (insensible à la casse) sur le nom ou le prénom."""
        pattern = {"$regex": re.escape(name), "$options": "i"}
        return self._find({"$or": [{"lastName": pattern}, {"firstName": pattern}]})

    def create(self, director: DirectorDTO) -> DirectorDTO:
        """Lève DuplicateKeyError si idDirector existe déjà."""
        self._collection.insert_one(director.toDict())
        return director

    def _find(self, query: dict) -> List[DirectorDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort("idDirector", ASCENDING)
        return [DirectorDTO.fromDict(doc) for doc in documents]