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
class ActorDTO(BaseDTO):
    idActor: int
    firstName: str
    lastName: str

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "ActorDTO":
        return cls(
            idActor=data["idActor"],
            firstName=data["firstName"],
            lastName=data["lastName"],
        )