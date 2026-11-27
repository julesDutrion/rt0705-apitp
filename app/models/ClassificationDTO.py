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
    """Classe qui représente une classification par âge."""

    minAge: int
    idClassification: Optional[int] = None
    ID_FIELDS = frozenset({"idClassification"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "ClassificationDTO":
        """
        Méthode qui crée une classification à partir d'un dictionnaire.

        :param data: Données de la classification, identifiant facultatif inclus.
        :return: DTO de la classification.
        :raises KeyError: Si l'âge minimum est absent.
        """
        return cls(
            idClassification=data.get("idClassification"),
            minAge=data["minAge"],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "ClassificationDTO":
        """
        Méthode qui crée une classification sans identifiant à partir d'un dictionnaire.

        :param data: Données de la classification.
        :return: DTO de la classification.
        :raises KeyError: Si l'âge minimum est absent.
        """
        return cls(minAge=data["minAge"])