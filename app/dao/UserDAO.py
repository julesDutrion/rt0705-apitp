from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import UserDTO

_NO_MONGO_ID = {"_id": 0}


class UserDAO:
    """Classe qui représente l'accès aux données des utilisateurs."""

    COLLECTION_NAME = "users"

    def __init__(self, database: Database) -> None:
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idUser", ASCENDING)], unique=True)
        self._collection.create_index([("login", ASCENDING)], unique=True)
        self._collection.create_index([("email", ASCENDING)], unique=True)

    def getAll(self) -> List[UserDTO]:
        """
        Méthode qui récupère tous les utilisateurs.

        :return: Liste des DTO d'utilisateurs.
        """
        return self._find({})

    def getById(self, idUser: int) -> Optional[UserDTO]:
        """
        Méthode qui récupère un utilisateur par son identifiant.

        :param idUser: Identifiant de l'utilisateur.
        :return: DTO de l'utilisateur ou None s'il est absent.
        """
        document = self._collection.find_one({"idUser": idUser}, _NO_MONGO_ID)
        return UserDTO.fromDict(document) if document else None

    def exists(self, idUser: int) -> bool:
        """
        Méthode qui vérifie l'existence d'un utilisateur.

        :param idUser: Identifiant de l'utilisateur.
        :return: True si l'utilisateur existe, sinon False.
        """
        return self._collection.count_documents({"idUser": idUser}, limit=1) > 0

    def getByLogin(self, login: str) -> Optional[UserDTO]:
        """
        Méthode qui récupère un utilisateur par son login.

        :param login: Login recherché.
        :return: DTO de l'utilisateur ou None s'il est absent.
        """
        document = self._collection.find_one(
            {"login": login}, _NO_MONGO_ID
        )
        return UserDTO.fromDict(document) if document else None

    def getByEmail(self, email: str) -> Optional[UserDTO]:
        """
        Méthode qui récupère un utilisateur par son adresse e-mail.

        :param email: Adresse e-mail recherchée.
        :return: DTO de l'utilisateur ou None s'il est absent.
        """
        document = self._collection.find_one(
            {"email": email}, _NO_MONGO_ID
        )
        return UserDTO.fromDict(document) if document else None

    def create(self, user: UserDTO) -> UserDTO:
        """
        Méthode qui enregistre un utilisateur.

        :param user: DTO de l'utilisateur à enregistrer.
        :return: DTO de l'utilisateur enregistré.
        :raises DuplicateKeyError: Si le login, l'e-mail ou l'identifiant existe.
        """
        if user.idUser is None:
            document = self._collection.find_one(
                {}, {"idUser": 1, "_id": 0}, sort=[("idUser", DESCENDING)]
            )
            nextId = (document["idUser"] + 1) if document else 1

            while self.exists(nextId):
                nextId += 1

            user.idUser = nextId

        self._collection.insert_one(user.toDict())
        return user

    def update(self, user: UserDTO) -> bool:
        """
        Méthode qui remplace les données d'un utilisateur.

        :param user: DTO contenant les données modifiées.
        :return: True si un utilisateur a été modifié, sinon False.
        """
        result = self._collection.replace_one(
            {"idUser": user.idUser}, user.toDict()
        )
        return result.matched_count == 1

    def delete(self, idUser: int) -> bool:
        """
        Méthode qui supprime un utilisateur.

        :param idUser: Identifiant de l'utilisateur.
        :return: True si un utilisateur a été supprimé, sinon False.
        """
        result = self._collection.delete_one({"idUser": idUser})
        return result.deleted_count == 1

    def _find(self, query: dict) -> List[UserDTO]:
        documents = self._collection.find(query, _NO_MONGO_ID).sort(
            "idUser", ASCENDING
        )
        return [UserDTO.fromDict(document) for document in documents]