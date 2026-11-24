from typing import Dict, List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import SupportTypeDTO


_NO_MONGO_ID = {"_id": 0}


class SupportTypeDAO:
    COLLECTION_NAME = "supportTypes"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idSupportType", ASCENDING)], unique=True)

    def getAll(self) -> List[SupportTypeDTO]:
        documents = self._collection.find({}, _NO_MONGO_ID).sort(
            "idSupportType", ASCENDING
        )
        return [SupportTypeDTO.fromDict(document) for document in documents]

    def getById(self, idSupportType: int) -> Optional[SupportTypeDTO]:
        document = self._collection.find_one(
            {"idSupportType": idSupportType}, _NO_MONGO_ID
        )
        return SupportTypeDTO.fromDict(document) if document else None

    def exists(self, idSupportType: int) -> bool:
        return self._collection.count_documents(
            {"idSupportType": idSupportType}, limit=1
        ) > 0

    def create(self, supportType: SupportTypeDTO) -> SupportTypeDTO:
        if supportType.idSupportType is None:
            latest = self._collection.find_one(
                {}, {"idSupportType": 1, "_id": 0},
                sort=[("idSupportType", DESCENDING)],
            )
            supportType.idSupportType = (
                latest["idSupportType"] + 1 if latest else 1
            )
        self._collection.insert_one(supportType.toDict())
        return supportType

    def update(self, supportType: SupportTypeDTO) -> bool:
        result = self._collection.replace_one(
            {"idSupportType": supportType.idSupportType},
            supportType.toDict(),
        )
        return result.matched_count == 1

    def delete(self, idSupportType: int) -> bool:
        result = self._collection.delete_one({"idSupportType": idSupportType})
        return result.deleted_count == 1
