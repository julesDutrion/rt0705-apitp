from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import ClassificationDTO

_NO_MONGO_ID = {"_id": 0}


class ClassificationDAO:
    """Classe qui représente l'accès aux données des classifications."""

    COLLECTION_NAME = "classifications"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idClassification", ASCENDING)], unique=True)

    def getAll(self) -> List[ClassificationDTO]:
        """
        Méthode qui récupère toutes les classifications.

        :return: Liste des DTO de classifications.
        """
        return self._find({})

    def getById(self, idClassification: int) -> Optional[ClassificationDTO]:
        """
        Méthode qui récupère une classification par son identifiant.

        :param idClassification: Identifiant de la classification.
        :return: DTO de la classification ou None si elle est absente.
        """
        document = self._collection.find_one(
            {"idClassification": idClassification}, _NO_MONGO_ID
        )
        return ClassificationDTO.fromDict(document) if document else None

    def exists(self, idClassification: int) -> bool:
        """
        Méthode qui vérifie l'existence d'une classification.

        :param idClassification: Identifiant de la classification.
        :return: True si la classification existe, sinon False.
        """
        query = {"idClassification": idClassification}
        return self._collection.count_documents(query, limit=1) > 0

    def getByMinAge(self, minAge: int) -> List[ClassificationDTO]:
        """
        Méthode qui récupère les classifications d'un âge minimum donné.

        :param minAge: Âge minimum recherché.
        :return: Liste des classifications correspondantes.
        """
        return self._find({"minAge": minAge})

    def getIdsAllowedForAge(self, age: int) -> List[int]:
        """
        Méthode qui récupère les identifiants autorisés pour un âge.

        :param age: Âge de référence.
        :return: Identifiants des classifications accessibles.
        """
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
        """
        Méthode qui enregistre une classification.

        :param classification: DTO de la classification à enregistrer.
        :return: DTO de la classification enregistrée.
        :raises DuplicateKeyError: Si l'identifiant existe déjà.
        """
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
        """
        Méthode qui remplace les données d'une classification.

        :param classification: DTO contenant les données modifiées.
        :return: True si une classification a été modifiée, sinon False.
        """
        result = self._collection.replace_one(
            {"idClassification": classification.idClassification},
            classification.toDict(),
        )
        return result.matched_count == 1

    def delete(self, idClassification: int) -> bool:
        """
        Méthode qui supprime une classification.

        :param idClassification: Identifiant de la classification.
        :return: True si une classification a été supprimée, sinon False.
        """
        result = self._collection.delete_one(
            {"idClassification": idClassification}
        )
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[ClassificationDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort(
            "idClassification", ASCENDING
        )
        return [ClassificationDTO.fromDict(doc) for doc in documents]