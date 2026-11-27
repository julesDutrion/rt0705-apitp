import re
from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import GenreDTO

_NO_MONGO_ID = {"_id": 0}


class GenreDAO:
    """Classe qui représente l'accès aux données des genres."""

    COLLECTION_NAME = "genres"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idGenre", ASCENDING)], unique=True)

    def getAll(self) -> List[GenreDTO]:
        """
        Méthode qui récupère tous les genres.

        :return: Liste des DTO de genres.
        """
        return self._find({})

    def getById(self, idGenre: int) -> Optional[GenreDTO]:
        """
        Méthode qui récupère un genre par son identifiant.

        :param idGenre: Identifiant du genre.
        :return: DTO du genre ou None s'il est absent.
        """
        document = self._collection.find_one({"idGenre": idGenre}, _NO_MONGO_ID)
        return GenreDTO.fromDict(document) if document else None

    def exists(self, idGenre: int) -> bool:
        """
        Méthode qui vérifie l'existence d'un genre.

        :param idGenre: Identifiant du genre.
        :return: True si le genre existe, sinon False.
        """
        return self._collection.count_documents({"idGenre": idGenre}, limit=1) > 0

    def searchByName(self, name: str) -> List[GenreDTO]:
        """
        Méthode qui recherche les genres par nom.

        :param name: Texte recherché.
        :return: Liste des genres correspondants.
        """
        pattern = {"$regex": re.escape(name), "$options": "i"}
        return self._find({"nameGenre": pattern})

    def create(self, genre: GenreDTO) -> GenreDTO:
        """
        Méthode qui enregistre un genre.

        :param genre: DTO du genre à enregistrer.
        :return: DTO du genre enregistré.
        :raises DuplicateKeyError: Si l'identifiant existe déjà.
        """
        if genre.idGenre is None:
            document = self._collection.find_one(
                {}, {"idGenre": 1, "_id": 0},
                sort=[("idGenre", DESCENDING)],
            )
            nextId = (document["idGenre"] + 1) if document else 1
            while self.exists(nextId):
                nextId += 1
            genre.idGenre = nextId
        self._collection.insert_one(genre.toDict())
        return genre

    def update(self, genre: GenreDTO) -> bool:
        """
        Méthode qui remplace les données d'un genre.

        :param genre: DTO contenant les données modifiées.
        :return: True si un genre a été modifié, sinon False.
        """
        result = self._collection.replace_one(
            {"idGenre": genre.idGenre}, genre.toDict()
        )
        return result.matched_count == 1

    def delete(self, idGenre: int) -> bool:
        """
        Méthode qui supprime un genre.

        :param idGenre: Identifiant du genre.
        :return: True si un genre a été supprimé, sinon False.
        """
        result = self._collection.delete_one({"idGenre": idGenre})
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[GenreDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort("idGenre", ASCENDING)
        return [GenreDTO.fromDict(doc) for doc in documents]