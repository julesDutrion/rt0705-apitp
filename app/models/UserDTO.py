from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from .BaseDTO import BaseDTO
from .RoleEnum import UserRole


@dataclass
class UserDTO(BaseDTO):
    """Classe qui représente un compte utilisateur."""

    role: UserRole
    login: str
    email: str
    passwordHash: str
    birthDate: date
    idUser: Optional[int] = None

    ID_FIELDS = frozenset({"idUser"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "UserDTO":
        """
        Méthode qui crée un utilisateur à partir d'un dictionnaire.

        :param data: Données du compte.
        :return: DTO de l'utilisateur.
        :raises KeyError: Si un champ obligatoire est absent.
        :raises ValueError: Si le rôle ou la date de naissance est invalide.
        """
        return cls(
            idUser=data.get("idUser"),
            role=UserRole(data["role"]),
            login=data["login"],
            email=data["email"],
            passwordHash=data["passwordHash"],
            birthDate=date.fromisoformat(data["birthDate"]),
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "UserDTO":
        """
        Méthode qui crée un utilisateur sans identifiant.

        :param data: Données du compte.
        :return: DTO de l'utilisateur.
        :raises KeyError: Si un champ obligatoire est absent.
        :raises ValueError: Si le rôle ou la date de naissance est invalide.
        """
        return cls(
            role=UserRole(data["role"]),
            login=data["login"],
            email=data["email"],
            passwordHash=data["passwordHash"],
            birthDate=date.fromisoformat(data["birthDate"]),
        )

    def toDict(self) -> Dict[str, Any]:
        """
        Méthode qui convertit l'utilisateur en dictionnaire.

        :return: Données du compte incluant son rôle.
        """
        data = super().toDict()
        data["role"] = self.role.value
        return data

    def calculateAge(self) -> int:
        """
        Méthode qui calcule l'âge de l'utilisateur à la date du jour.

        :return: Âge en années.
        """
        today = date.today()
        age = today.year - self.birthDate.year

        if (today.month, today.day) < (
            self.birthDate.month,
            self.birthDate.day
        ):
            age -= 1

        return age

    def toPublicDict(self) -> Dict[str, Any]:
        """
        Méthode qui prépare les données utilisateur destinées au client.

        :return: Données publiques du compte sans hash de mot de passe.
        """
        data = self.toDict()
        data.pop("passwordHash", None)
        data["birthDate"] = self.birthDate.isoformat()
        data["age"] = self.calculateAge()
        return data