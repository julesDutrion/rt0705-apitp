"""DTO des exemplaires physiques et des accès numériques aux films."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .BaseDTO import BaseDTO
from .SupportTypeDTO import SupportTypeDTO


@dataclass
class SupportDTO(BaseDTO):
    idFilm: str
    idSupportType: int
    location: Optional[str] = None
    url: Optional[str] = None
    idSupport: Optional[int] = None
    supportType: Optional[SupportTypeDTO] = None
    ID_FIELDS = frozenset({"idSupport"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "SupportDTO":
        return cls(
            idSupport=data.get("idSupport"),
            idFilm=data["idFilm"],
            idSupportType=data["idSupportType"],
            location=data.get("location"),
            url=data.get("url"),
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "SupportDTO":
        return cls.fromDict({**data, "idSupport": None})
