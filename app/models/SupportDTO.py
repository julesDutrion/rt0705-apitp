"""DTO des exemplaires physiques et des accès numériques aux films."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .BaseDTO import BaseDTO
from .SupportTypeDTO import SupportTypeDTO


@dataclass
class SupportDTO(BaseDTO):
    """Classe qui représente un support physique ou numérique associé à un film."""

    idFilm: str
    idSupportType: int
    location: Optional[str] = None
    url: Optional[str] = None
    idSupport: Optional[int] = None
    supportType: Optional[SupportTypeDTO] = None
    ID_FIELDS = frozenset({"idSupport"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "SupportDTO":
        """
        Méthode qui crée un support à partir d'un dictionnaire.

        :param data: Données du support.
        :return: DTO du support.
        :raises KeyError: Si le film ou le type de support est absent.
        """
        return cls(
            idSupport=data.get("idSupport"),
            idFilm=data["idFilm"],
            idSupportType=data["idSupportType"],
            location=data.get("location"),
            url=data.get("url"),
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "SupportDTO":
        """
        Méthode qui crée un support sans identifiant à partir d'un dictionnaire.

        :param data: Données du support.
        :return: DTO du support.
        :raises KeyError: Si le film ou le type de support est absent.
        """
        return cls.fromDict({**data, "idSupport": None})
