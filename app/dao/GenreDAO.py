import re
from typing import List, Optional

from pymongo import ASCENDING
from pymongo.database import Database

from ..models.GenreDTO import GenreDTO

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
        """Lève DuplicateKeyError si idGenre existe déjà."""
        self._collection.insert_one(genre.toDict())
        return genre

    def _find(self, query: dict) -> List[GenreDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort("idGenre", ASCENDING)
        return [GenreDTO.fromDict(doc) for doc in documents]