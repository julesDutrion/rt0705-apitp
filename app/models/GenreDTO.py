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
    """Classe qui représente un genre de film."""

    nameGenre: str
    idGenre: Optional[int] = None
    ID_FIELDS = frozenset({"idGenre"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "GenreDTO":
        """
        Méthode qui crée un genre à partir d'un dictionnaire.

        :param data: Données du genre, identifiant facultatif inclus.
        :return: DTO du genre.
        :raises KeyError: Si le nom du genre est absent.
        """
        return cls(idGenre=data.get("idGenre"), nameGenre=data["nameGenre"])

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "GenreDTO":
        """
        Méthode qui crée un genre sans identifiant à partir d'un dictionnaire.

        :param data: Données du genre.
        :return: DTO du genre.
        :raises KeyError: Si le nom du genre est absent.
        """
        return cls(nameGenre=data["nameGenre"])
