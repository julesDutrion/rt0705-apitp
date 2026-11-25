from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from .BaseDTO import BaseDTO
from .RoleEnum import UserRole


@dataclass
class UserDTO(BaseDTO):
    role: UserRole
    login: str
    email: str
    passwordHash: str
    birthDate: date
    idUser: Optional[int] = None

    ID_FIELDS = frozenset({"idUser"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "UserDTO":
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
        return cls(
            role=UserRole(data["role"]),
            login=data["login"],
            email=data["email"],
            passwordHash=data["passwordHash"],
            birthDate=date.fromisoformat(data["birthDate"]),
        )

    def calculateAge(self) -> int:
        today = date.today()
        age = today.year - self.birthDate.year

        if (today.month, today.day) < (
            self.birthDate.month,
            self.birthDate.day
        ):
            age -= 1

        return age

    def toPublicDict(self) -> Dict[str, Any]:
        """Version à renvoyer au client : sans le hash du mot de passe."""
        data = self.toDict()
        data.pop("passwordHash", None)
        data["birthDate"] = self.birthDate.isoformat()
        data["age"] = self.calculateAge()
        return data