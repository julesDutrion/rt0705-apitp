"""DTOs du package Model (vidéothèque).

Les noms d'attributs suivent le diagramme de classes (camelCase) afin que
les clés JSON de l'API correspondent exactement au modèle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date
from typing import Any, Dict, List, Optional
from models import BaseDTO, RoleDTO



@dataclass
class UserDTO(BaseDTO):
    role: RoleDTO
    userName: str
    email: str
    passwordHash: str
    age: int

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "UserDTO":
        return cls(
            role=RoleDTO.fromDict(data["role"]),
            userName=data["userName"],
            email=data["email"],
            passwordHash=data["passwordHash"],
            age=data["age"],
        )

    def toPublicDict(self) -> Dict[str, Any]:
        """Version à renvoyer au client : sans le hash du mot de passe."""
        data = self.toDict()
        data.pop("passwordHash", None)
        return data