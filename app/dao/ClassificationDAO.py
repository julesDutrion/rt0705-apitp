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

    def getIdsAllowedForAge(self, age: int) -> List[int]:
        documents = self._collection.find(
            {
                "minAge": {
                    "$type": "number",
                    "$gte": 0,
                    "$lte": age,
                }
            },
            {"idClassification": 1, "minAge": 1, "_id": 0},
        )
        return [
            document["idClassification"]
            for document in documents
            if type(document.get("minAge")) is int
            and 0 <= document["minAge"] <= age
            and type(document.get("idClassification")) is int
            and document["idClassification"] > 0
        ]

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

    def update(self, classification: ClassificationDTO) -> bool:
        result = self._collection.replace_one(
            {"idClassification": classification.idClassification},
            classification.toDict(),
        )
        return result.matched_count == 1

    def delete(self, idClassification: int) -> bool:
        result = self._collection.delete_one(
            {"idClassification": idClassification}
        )
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[ClassificationDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort(
            "idClassification", ASCENDING
        )
        return [ClassificationDTO.fromDict(doc) for doc in documents]