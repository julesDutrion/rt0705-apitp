import re
from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import DirectorDTO

_NO_MONGO_ID = {"_id": 0}

'''
    Classe représentant un DAO pour les réalisateurs
'''
class DirectorDAO:
    """Classe qui représente l'accès aux données des réalisateurs."""

    COLLECTION_NAME = "directors"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idDirector", ASCENDING)], unique=True)

    def getAll(self) -> List[DirectorDTO]:
        """
        Méthode qui récupère tous les réalisateurs.

        :return: Liste des DTO de réalisateurs.
        """
        return self._find({})

    def getById(self, idDirector: int) -> Optional[DirectorDTO]:
        """
        Méthode qui récupère un réalisateur par son identifiant.

        :param idDirector: Identifiant du réalisateur.
        :return: DTO du réalisateur ou None s'il est absent.
        """
        document = self._collection.find_one({"idDirector": idDirector}, _NO_MONGO_ID)
        return DirectorDTO.fromDict(document) if document else None

    def exists(self, idDirector: int) -> bool:
        """
        Méthode qui vérifie l'existence d'un réalisateur.

        :param idDirector: Identifiant du réalisateur.
        :return: True si le réalisateur existe, sinon False.
        """
        return self._collection.count_documents({"idDirector": idDirector}, limit=1) > 0

    def searchByName(self, name: str) -> List[DirectorDTO]:
        """
        Méthode qui recherche les réalisateurs par nom ou prénom.

        :param name: Texte recherché.
        :return: Liste des réalisateurs correspondants.
        """
        pattern = {"$regex": re.escape(name), "$options": "i"}
        return self._find({"$or": [{"lastName": pattern}, {"firstName": pattern}]})

    def create(self, director: DirectorDTO) -> DirectorDTO:
        """
        Méthode qui enregistre un réalisateur.

        :param director: DTO du réalisateur à enregistrer.
        :return: DTO du réalisateur enregistré.
        :raises DuplicateKeyError: Si l'identifiant existe déjà.
        """
        if director.idDirector is None:
            document = self._collection.find_one(
                {}, {"idDirector": 1, "_id": 0},
                sort=[("idDirector", DESCENDING)],
            )
            nextId = (document["idDirector"] + 1) if document else 1
            while self.exists(nextId):
                nextId += 1
            director.idDirector = nextId
        self._collection.insert_one(director.toDict())
        return director

    def update(self, director: DirectorDTO) -> bool:
        """
        Méthode qui remplace les données d'un réalisateur.

        :param director: DTO contenant les données modifiées.
        :return: True si un réalisateur a été modifié, sinon False.
        """
        result = self._collection.replace_one(
            {"idDirector": director.idDirector}, director.toDict()
        )
        return result.matched_count == 1

    def delete(self, idDirector: int) -> bool:
        """
        Méthode qui supprime un réalisateur.

        :param idDirector: Identifiant du réalisateur.
        :return: True si un réalisateur a été supprimé, sinon False.
        """
        result = self._collection.delete_one({"idDirector": idDirector})
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[DirectorDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort("idDirector", ASCENDING)
        return [DirectorDTO.fromDict(doc) for doc in documents]