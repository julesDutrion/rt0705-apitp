import re
from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import LanguageDTO

_NO_MONGO_ID = {"_id": 0}


class LanguageDAO:
    """Classe qui représente l'accès aux données des langues."""

    COLLECTION_NAME = "languages"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idLanguage", ASCENDING)], unique=True)

    def getAll(self) -> List[LanguageDTO]:
        """
        Méthode qui récupère toutes les langues.

        :return: Liste des DTO de langues.
        """
        documents = self._collection.find({}, _NO_MONGO_ID).sort("idLanguage", ASCENDING)
        return [LanguageDTO.fromDict(doc) for doc in documents]

    def getById(self, idLanguage: int) -> Optional[LanguageDTO]:
        """
        Méthode qui récupère une langue par son identifiant.

        :param idLanguage: Identifiant de la langue.
        :return: DTO de la langue ou None si elle est absente.
        """
        document = self._collection.find_one({"idLanguage": idLanguage}, _NO_MONGO_ID)
        return LanguageDTO.fromDict(document) if document else None

    def exists(self, idLanguage: int) -> bool:
        """
        Méthode qui vérifie l'existence d'une langue.

        :param idLanguage: Identifiant de la langue.
        :return: True si la langue existe, sinon False.
        """
        return self._collection.count_documents({"idLanguage": idLanguage}, limit=1) > 0

    def getByCode(self, code: str) -> Optional[LanguageDTO]:
        """
        Méthode qui récupère une langue par son code.

        :param code: Code de la langue.
        :return: DTO de la langue ou None si elle est absente.
        """
        document = self._collection.find_one(
            {"code": {"$regex": f"^{re.escape(code)}$", "$options": "i"}},
            _NO_MONGO_ID,
        )
        return LanguageDTO.fromDict(document) if document else None

    def searchByName(self, name: str) -> List[LanguageDTO]:
        """
        Méthode qui recherche les langues par nom.

        :param name: Texte recherché.
        :return: Liste des langues correspondantes.
        """
        pattern = {"$regex": re.escape(name), "$options": "i"}
        documents = self._collection.find({"name": pattern}, _NO_MONGO_ID).sort(
            "idLanguage", ASCENDING
        )
        return [LanguageDTO.fromDict(document) for document in documents]

    def create(self, language: LanguageDTO) -> LanguageDTO:
        """
        Méthode qui enregistre une langue.

        :param language: DTO de la langue à enregistrer.
        :return: DTO de la langue enregistrée.
        :raises DuplicateKeyError: Si l'identifiant existe déjà.
        """
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
        """
        Méthode qui remplace les données d'une langue.

        :param language: DTO contenant les données modifiées.
        :return: True si une langue a été modifiée, sinon False.
        """
        language.code = language.code.lower()
        result = self._collection.replace_one(
            {"idLanguage": language.idLanguage}, language.toDict()
        )
        return result.matched_count == 1

    def delete(self, idLanguage: int) -> bool:
        """
        Méthode qui supprime une langue.

        :param idLanguage: Identifiant de la langue.
        :return: True si une langue a été supprimée, sinon False.
        """
        result = self._collection.delete_one({"idLanguage": idLanguage})
        return result.deleted_count == 1