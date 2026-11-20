import re
from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import GenreDTO

_NO_MONGO_ID = {"_id": 0}


class GenreDAO:
    COLLECTION_NAME = "genres"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idGenre", ASCENDING)], unique=True)

    def getAll(self) -> List[GenreDTO]:
        return self._find({})

    def getById(self, idGenre: int) -> Optional[GenreDTO]:
        document = self._collection.find_one({"idGenre": idGenre}, _NO_MONGO_ID)
        return GenreDTO.fromDict(document) if document else None

    def exists(self, idGenre: int) -> bool:
        return self._collection.count_documents({"idGenre": idGenre}, limit=1) > 0

    def searchByName(self, name: str) -> List[GenreDTO]:
        pattern = {"$regex": re.escape(name), "$options": "i"}
        return self._find({"nameGenre": pattern})

    def create(self, genre: GenreDTO) -> GenreDTO:
        """Génère un identifiant entier absent de la collection."""
        if genre.idGenre is None:
            document = self._collection.find_one(
                {}, {"idGenre": 1, "_id": 0},
                sort=[("idGenre", DESCENDING)],
            )
            nextId = (document["idGenre"] + 1) if document else 1
            while self.exists(nextId):
                nextId += 1
            genre.idGenre = nextId
        self._collection.insert_one(genre.toDict())
        return genre

    def _find(self, query: dict) -> List[GenreDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort("idGenre", ASCENDING)
        return [GenreDTO.fromDict(doc) for doc in documents]