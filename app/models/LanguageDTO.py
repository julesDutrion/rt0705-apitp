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
class LanguageDTO(BaseDTO):
    """Classe qui représente une langue du catalogue."""

    code: str
    name: str
    idLanguage: Optional[int] = None
    ID_FIELDS = frozenset({"idLanguage"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "LanguageDTO":
        """
        Méthode qui crée une langue à partir d'un dictionnaire.

        :param data: Données de la langue, identifiant facultatif inclus.
        :return: DTO de la langue.
        :raises KeyError: Si le code ou le nom est absent.
        """
        return cls(
            idLanguage=data.get("idLanguage"),
            code=data["code"],
            name=data["name"],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "LanguageDTO":
        """
        Méthode qui crée une langue sans identifiant à partir d'un dictionnaire.

        :param data: Données de la langue.
        :return: DTO de la langue.
        :raises KeyError: Si le code ou le nom est absent.
        """
        return cls(code=data["code"], name=data["name"])