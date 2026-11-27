from datetime import datetime
from typing import Dict, List, Optional, Set

from pymongo import ASCENDING, ReturnDocument
from pymongo.database import Database

from ..models import LoanDTO


_NO_MONGO_ID = {"_id": 0}
_ACTIVE_LOAN_FILTER = {"actualReturnDate": None}


class LoanDAO:
    """Classe qui représente l'accès aux données des emprunts."""

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
        """
        Méthode qui récupère tous les emprunts.

        :return: Liste des DTO d'emprunts.
        """
        documents = self._collection.find({}, _NO_MONGO_ID).sort(
            "idLoan", ASCENDING
        )
        return [LoanDTO.fromDict(document) for document in documents]

    def getById(self, idLoan: int) -> Optional[LoanDTO]:
        """
        Méthode qui récupère un emprunt par son identifiant.

        :param idLoan: Identifiant de l'emprunt.
        :return: DTO de l'emprunt ou None s'il est absent.
        """
        document = self._collection.find_one(
            {"idLoan": idLoan}, _NO_MONGO_ID
        )
        return LoanDTO.fromDict(document) if document else None

    def getByUserId(self, idUser: int) -> List[LoanDTO]:
        """
        Méthode qui récupère les emprunts d'un utilisateur.

        :param idUser: Identifiant de l'utilisateur.
        :return: Liste des DTO d'emprunts de l'utilisateur.
        """
        documents = self._collection.find(
            {"idUser": idUser}, _NO_MONGO_ID
        ).sort("idLoan", ASCENDING)
        return [LoanDTO.fromDict(document) for document in documents]

    def getByIdAndUserId(
        self, idLoan: int, idUser: int
    ) -> Optional[LoanDTO]:
        """
        Méthode qui récupère un emprunt appartenant à un utilisateur.

        :param idLoan: Identifiant de l'emprunt.
        :param idUser: Identifiant du propriétaire.
        :return: DTO de l'emprunt ou None s'il n'appartient pas à l'utilisateur.
        """
        document = self._collection.find_one(
            {"idLoan": idLoan, "idUser": idUser}, _NO_MONGO_ID
        )
        return LoanDTO.fromDict(document) if document else None

    def hasActiveLoanForSupport(self, idPhysicalSupport: int) -> bool:
        """
        Méthode qui vérifie si un support possède un emprunt actif.

        :param idPhysicalSupport: Identifiant du support physique.
        :return: True si un emprunt actif existe, sinon False.
        """
        return self._collection.count_documents(
            {
                "idPhysicalSupport": idPhysicalSupport,
                **_ACTIVE_LOAN_FILTER,
            },
            limit=1,
        ) > 0

    def getActivePhysicalSupportIds(self) -> Set[int]:
        """
        Méthode qui récupère les supports associés à un emprunt actif.

        :return: Ensemble des identifiants de supports physiques empruntés.
        """
        return set(
            self._collection.distinct(
                "idPhysicalSupport", _ACTIVE_LOAN_FILTER
            )
        )

    def nextId(self) -> int:
        """
        Méthode qui génère le prochain identifiant d'emprunt.

        :return: Identifiant unique généré.
        """
        counter = self._counterCollection.find_one_and_update(
            {"_id": self.COUNTER_ID},
            {"$inc": {"sequence": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return counter["sequence"]

    def create(self, loan: LoanDTO) -> LoanDTO:
        """
        Méthode qui enregistre un emprunt.

        :param loan: DTO de l'emprunt à enregistrer.
        :return: DTO de l'emprunt enregistré.
        :raises DuplicateKeyError: Si le support possède déjà un emprunt actif.
        """
        self._collection.insert_one(self._toDocument(loan))
        return loan

    def markReturned(
        self, idLoan: int, actualReturnDate: datetime
    ) -> Optional[LoanDTO]:
        """
        Méthode qui renseigne la date de retour d'un emprunt actif.

        :param idLoan: Identifiant de l'emprunt.
        :param actualReturnDate: Date effective du retour.
        :return: Emprunt modifié ou None s'il est absent ou déjà retourné.
        """
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
