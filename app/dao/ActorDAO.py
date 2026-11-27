import re
from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import ActorDTO

_NO_MONGO_ID = {"_id": 0}


class ActorDAO:
    """Classe qui représente l'accès aux données des acteurs."""

    COLLECTION_NAME = "actors"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idActor", ASCENDING)], unique=True)

    def getAll(self) -> List[ActorDTO]:
        """
        Méthode qui récupère tous les acteurs.

        :return: Liste des DTO d'acteurs.
        """
        return self._find({})

    def getById(self, idActor: int) -> Optional[ActorDTO]:
        """
        Méthode qui récupère un acteur à partir de son identifiant.

        :param idActor: Identifiant de l'acteur.
        :return: DTO de l'acteur ou None s'il est absent.
        """
        document = self._collection.find_one({"idActor": idActor}, _NO_MONGO_ID)
        return ActorDTO.fromDict(document) if document else None

    def exists(self, idActor: int) -> bool:
        """
        Méthode qui vérifie l'existence d'un acteur.

        :param idActor: Identifiant de l'acteur.
        :return: True si l'acteur existe, sinon False.
        """
        return self._collection.count_documents({"idActor": idActor}, limit=1) > 0

    def searchByName(self, name: str) -> List[ActorDTO]:
        """
        Méthode qui recherche les acteurs par prénom ou nom.

        :param name: Texte recherché.
        :return: Liste des acteurs correspondants.
        """
        pattern = {"$regex": re.escape(name), "$options": "i"}
        return self._find({"$or": [{"firstName": pattern}, {"lastName": pattern}]})

    def create(self, actor: ActorDTO) -> ActorDTO:
        """
        Méthode qui enregistre un acteur.

        :param actor: DTO de l'acteur à enregistrer.
        :return: DTO de l'acteur enregistré.
        :raises DuplicateKeyError: Si l'identifiant existe déjà.
        """
        if actor.idActor is None:
            document = self._collection.find_one(
                {}, {"idActor": 1, "_id": 0}, sort=[("idActor", DESCENDING)]
            )
            nextId = (document["idActor"] + 1) if document else 1
            while self.exists(nextId):
                nextId += 1
            actor.idActor = nextId
        self._collection.insert_one(actor.toDict())
        return actor

    def update(self, actor: ActorDTO) -> bool:
        """
        Méthode qui remplace les données d'un acteur.

        :param actor: DTO contenant les données modifiées.
        :return: True si un acteur a été modifié, sinon False.
        """
        result = self._collection.replace_one(
            {"idActor": actor.idActor}, actor.toDict()
        )
        return result.matched_count == 1

    def delete(self, idActor: int) -> bool:
        """
        Méthode qui supprime un acteur.

        :param idActor: Identifiant de l'acteur.
        :return: True si un acteur a été supprimé, sinon False.
        """
        result = self._collection.delete_one({"idActor": idActor})
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[ActorDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort(
            "idActor", ASCENDING
        )
        return [ActorDTO.fromDict(document) for document in documents]
