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
class ActorDTO(BaseDTO):
    firstName: str
    lastName: str
    idActor: Optional[int] = None
    ID_FIELDS = frozenset({"idActor"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "ActorDTO":
        return cls(
            idActor=data.get("idActor"),
            firstName=data["firstName"],
            lastName=data["lastName"],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "ActorDTO":
        return cls(firstName=data["firstName"], lastName=data["lastName"])