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
class GenreDTO(BaseDTO):
    nameGenre: str
    idGenre: Optional[int] = None
    ID_FIELDS = frozenset({"idGenre"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "GenreDTO":
        return cls(idGenre=data.get("idGenre"), nameGenre=data["nameGenre"])

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "GenreDTO":
        return cls(nameGenre=data["nameGenre"])
