"""DTOs du package Model (vidéothèque).

Les noms d'attributs suivent le diagramme de classes (camelCase) afin que
les clés JSON de l'API correspondent exactement au modèle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date
from typing import Any, Dict, List, Optional
from .BaseDTO import BaseDTO

@dataclass
class RoleDTO(BaseDTO):
    roleName: str
    idRole: Optional[int] = None
    ID_FIELDS = frozenset({"idRole"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "RoleDTO":
        return cls(idRole=data.get("idRole"), roleName=data["roleName"])

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "RoleDTO":
        return cls(roleName=data["roleName"])