"""DTO des types de supports disponibles."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .BaseDTO import BaseDTO


@dataclass
class SupportTypeDTO(BaseDTO):
    """Classe qui représente un type de support disponible."""

    name: str
    mode: str
    idSupportType: Optional[int] = None
    ID_FIELDS = frozenset({"idSupportType"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "SupportTypeDTO":
        """
        Méthode qui crée un type de support à partir d'un dictionnaire.

        :param data: Données du type de support, identifiant facultatif inclus.
        :return: DTO du type de support.
        :raises KeyError: Si le nom ou le mode est absent.
        """
        return cls(
            idSupportType=data.get("idSupportType"),
            name=data["name"],
            mode=data["mode"],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "SupportTypeDTO":
        """
        Méthode qui crée un type de support sans identifiant.

        :param data: Données du type de support.
        :return: DTO du type de support.
        :raises KeyError: Si le nom ou le mode est absent.
        """
        return cls(name=data["name"], mode=data["mode"])
