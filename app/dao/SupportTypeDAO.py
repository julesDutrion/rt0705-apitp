from typing import Dict, List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import SupportTypeDTO


_NO_MONGO_ID = {"_id": 0}


class SupportTypeDAO:
    """Classe qui représente l'accès aux données des types de supports."""

    COLLECTION_NAME = "supportTypes"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idSupportType", ASCENDING)], unique=True)

    def getAll(self) -> List[SupportTypeDTO]:
        """
        Méthode qui récupère tous les types de supports.

        :return: Liste des DTO de types de supports.
        """
        documents = self._collection.find({}, _NO_MONGO_ID).sort(
            "idSupportType", ASCENDING
        )
        return [SupportTypeDTO.fromDict(document) for document in documents]

    def getById(self, idSupportType: int) -> Optional[SupportTypeDTO]:
        """
        Méthode qui récupère un type de support par son identifiant.

        :param idSupportType: Identifiant du type de support.
        :return: DTO du type ou None s'il est absent.
        """
        document = self._collection.find_one(
            {"idSupportType": idSupportType}, _NO_MONGO_ID
        )
        return SupportTypeDTO.fromDict(document) if document else None

    def exists(self, idSupportType: int) -> bool:
        """
        Méthode qui vérifie l'existence d'un type de support.

        :param idSupportType: Identifiant du type de support.
        :return: True si le type existe, sinon False.
        """
        return self._collection.count_documents(
            {"idSupportType": idSupportType}, limit=1
        ) > 0

    def create(self, supportType: SupportTypeDTO) -> SupportTypeDTO:
        """
        Méthode qui enregistre un type de support.

        :param supportType: DTO du type de support à enregistrer.
        :return: DTO du type de support enregistré.
        :raises DuplicateKeyError: Si l'identifiant existe déjà.
        """
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
        """
        Méthode qui remplace un type de support.

        :param supportType: DTO contenant les données modifiées.
        :return: True si un type a été modifié, sinon False.
        """
        result = self._collection.replace_one(
            {"idSupportType": supportType.idSupportType},
            supportType.toDict(),
        )
        return result.matched_count == 1

    def delete(self, idSupportType: int) -> bool:
        """
        Méthode qui supprime un type de support.

        :param idSupportType: Identifiant du type de support.
        :return: True si un type a été supprimé, sinon False.
        """
        result = self._collection.delete_one({"idSupportType": idSupportType})
        return result.deleted_count == 1
