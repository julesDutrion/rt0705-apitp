import re
from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import LanguageDTO

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
        document = self._collection.find_one(
            {"code": {"$regex": f"^{re.escape(code)}$", "$options": "i"}},
            _NO_MONGO_ID,
        )
        return LanguageDTO.fromDict(document) if document else None

    def searchByName(self, name: str) -> List[LanguageDTO]:
        pattern = {"$regex": re.escape(name), "$options": "i"}
        documents = self._collection.find({"name": pattern}, _NO_MONGO_ID).sort(
            "idLanguage", ASCENDING
        )
        return [LanguageDTO.fromDict(document) for document in documents]

    def create(self, language: LanguageDTO) -> LanguageDTO:
        """Génère un identifiant entier absent de la collection."""
        if language.idLanguage is None:
            document = self._collection.find_one(
                {}, {"idLanguage": 1, "_id": 0},
                sort=[("idLanguage", DESCENDING)],
            )
            nextId = (document["idLanguage"] + 1) if document else 1
            while self.exists(nextId):
                nextId += 1
            language.idLanguage = nextId
        self._collection.insert_one(language.toDict())
        return language

    def update(self, language: LanguageDTO) -> bool:
        language.code = language.code.lower()
        result = self._collection.replace_one(
            {"idLanguage": language.idLanguage}, language.toDict()
        )
        return result.matched_count == 1

    def delete(self, idLanguage: int) -> bool:
        result = self._collection.delete_one({"idLanguage": idLanguage})
        return result.deleted_count == 1