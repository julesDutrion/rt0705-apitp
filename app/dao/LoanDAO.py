from datetime import datetime
from typing import Dict, List, Optional

from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database

from ..models import LoanDTO


_NO_MONGO_ID = {"_id": 0}
_ACTIVE_LOAN_FILTER = {"actualReturnDate": None}


class LoanDAO:
    COLLECTION_NAME = "loans"
    COUNTER_ID = "loan"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._counterCollection = database["counters"]
        self._collection.create_index(
            [("idLoan", ASCENDING)], unique=True
        )
        self._collection.create_index(
            [("idUser", ASCENDING), ("idLoan", ASCENDING)]
        )
        self._collection.create_index(
            [("idPhysicalSupport", ASCENDING)],
            unique=True,
            partialFilterExpression=_ACTIVE_LOAN_FILTER,
            name="one_active_loan_per_physical_support",
        )

    def getAll(self) -> List[LoanDTO]:
        documents = self._collection.find({}, _NO_MONGO_ID).sort(
            "idLoan", ASCENDING
        )
        return [LoanDTO.fromDict(document) for document in documents]

    def getById(self, idLoan: int) -> Optional[LoanDTO]:
        document = self._collection.find_one(
            {"idLoan": idLoan}, _NO_MONGO_ID
        )
        return LoanDTO.fromDict(document) if document else None

    def getByUserId(self, idUser: int) -> List[LoanDTO]:
        documents = self._collection.find(
            {"idUser": idUser}, _NO_MONGO_ID
        ).sort("idLoan", ASCENDING)
        return [LoanDTO.fromDict(document) for document in documents]

    def getByIdAndUserId(
        self, idLoan: int, idUser: int
    ) -> Optional[LoanDTO]:
        document = self._collection.find_one(
            {"idLoan": idLoan, "idUser": idUser}, _NO_MONGO_ID
        )
        return LoanDTO.fromDict(document) if document else None

    def hasActiveLoanForSupport(self, idPhysicalSupport: int) -> bool:
        return self._collection.count_documents(
            {
                "idPhysicalSupport": idPhysicalSupport,
                **_ACTIVE_LOAN_FILTER,
            },
            limit=1,
        ) > 0

    def nextId(self) -> int:
        counter = self._counterCollection.find_one_and_update(
            {"_id": self.COUNTER_ID},
            {"$inc": {"sequence": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return counter["sequence"]

    def create(self, loan: LoanDTO) -> LoanDTO:
        self._collection.insert_one(self._toDocument(loan))
        return loan

    def markReturned(
        self, idLoan: int, actualReturnDate: datetime
    ) -> Optional[LoanDTO]:
        document = self._collection.find_one_and_update(
            {"idLoan": idLoan, **_ACTIVE_LOAN_FILTER},
            {"$set": {"actualReturnDate": actualReturnDate}},
            projection=_NO_MONGO_ID,
            return_document=ReturnDocument.AFTER,
        )
        return LoanDTO.fromDict(document) if document else None

    @staticmethod
    def _toDocument(loan: LoanDTO) -> Dict[str, object]:
        return {
            "idLoan": loan.idLoan,
            "idUser": loan.idUser,
            "idPhysicalSupport": loan.idPhysicalSupport,
            "startDate": loan.startDate,
            "expectedReturnDate": loan.expectedReturnDate,
            "actualReturnDate": loan.actualReturnDate,
        }
