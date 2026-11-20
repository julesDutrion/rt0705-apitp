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
class ClassificationDTO(BaseDTO):
    minAge: int
    idClassification: Optional[int] = None
    ID_FIELDS = frozenset({"idClassification"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "ClassificationDTO":
        return cls(
            idClassification=data.get("idClassification"),
            minAge=data["minAge"],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "ClassificationDTO":
        return cls(minAge=data["minAge"])