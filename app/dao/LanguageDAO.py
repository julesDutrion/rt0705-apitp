from typing import List, Optional

from pymongo import ASCENDING
from pymongo.database import Database

from ..models.LanguageDTO import LanguageDTO

_NO_MONGO_ID = {"_id": 0}


class LanguageDAO:
    COLLECTION_NAME = "languages"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idLanguage", ASCENDING)], unique=True)

    def getAll(self) -> List[LanguageDTO]:
        documents = self._collection.find({}, _NO_MONGO_ID).sort("idLanguage", ASCENDING)
        return [LanguageDTO.fromDict(doc) for doc in documents]

    def getById(self, idLanguage: int) -> Optional[LanguageDTO]:
        document = self._collection.find_one({"idLanguage": idLanguage}, _NO_MONGO_ID)
        return LanguageDTO.fromDict(document) if document else None

    def exists(self, idLanguage: int) -> bool:
        return self._collection.count_documents({"idLanguage": idLanguage}, limit=1) > 0

    def getByCode(self, code: str) -> Optional[LanguageDTO]:
        """Ex. 'fr', 'en'."""
        document = self._collection.find_one({"code": code.lower()}, _NO_MONGO_ID)
        return LanguageDTO.fromDict(document) if document else None

    def create(self, language: LanguageDTO) -> LanguageDTO:
        """Lève DuplicateKeyError si idLanguage existe déjà."""
        self._collection.insert_one(language.toDict())
        return language