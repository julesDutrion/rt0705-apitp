"""DTO des types de supports disponibles."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .BaseDTO import BaseDTO


@dataclass
class SupportTypeDTO(BaseDTO):
    name: str
    mode: str
    idSupportType: Optional[int] = None
    ID_FIELDS = frozenset({"idSupportType"})

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "SupportTypeDTO":
        return cls(
            idSupportType=data.get("idSupportType"),
            name=data["name"],
            mode=data["mode"],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "SupportTypeDTO":
        return cls(name=data["name"], mode=data["mode"])
