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
class DirectorDTO(BaseDTO):
    lastName: str
    firstName: str
    idDirector: Optional[int] = None
    ID_FIELDS = frozenset({"idDirector"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "DirectorDTO":
        return cls(
            idDirector=data.get("idDirector"),
            lastName=data["lastName"],
            firstName=data["firstName"],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "DirectorDTO":
        return cls(lastName=data["lastName"], firstName=data["firstName"])