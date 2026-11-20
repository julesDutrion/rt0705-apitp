from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import ClassificationDTO

_NO_MONGO_ID = {"_id": 0}


class ClassificationDAO:
    COLLECTION_NAME = "classifications"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idClassification", ASCENDING)], unique=True)

    def getAll(self) -> List[ClassificationDTO]:
        return self._find({})

    def getById(self, idClassification: int) -> Optional[ClassificationDTO]:
        document = self._collection.find_one(
            {"idClassification": idClassification}, _NO_MONGO_ID
        )
        return ClassificationDTO.fromDict(document) if document else None

    def exists(self, idClassification: int) -> bool:
        query = {"idClassification": idClassification}
        return self._collection.count_documents(query, limit=1) > 0

    def getByMinAge(self, minAge: int) -> List[ClassificationDTO]:
        return self._find({"minAge": minAge})

    def create(self, classification: ClassificationDTO) -> ClassificationDTO:
        """Génère un identifiant entier absent de la collection."""
        if classification.idClassification is None:
            document = self._collection.find_one(
                {}, {"idClassification": 1, "_id": 0},
                sort=[("idClassification", DESCENDING)],
            )
            nextId = (document["idClassification"] + 1) if document else 1
            while self.exists(nextId):
                nextId += 1
            classification.idClassification = nextId
        self._collection.insert_one(classification.toDict())
        return classification

    def _find(self, query: dict) -> List[ClassificationDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort(
            "idClassification", ASCENDING
        )
        return [ClassificationDTO.fromDict(doc) for doc in documents]