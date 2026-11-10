"""DTOs du package Model (vidéothèque).

Les noms d'attributs suivent le diagramme de classes (camelCase) afin que
les clés JSON de l'API correspondent exactement au modèle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date
from typing import Any, Dict, List, Optional
class BaseDTO:
    """Fournit la sérialisation commune (dict / JSON / MongoDB)."""

    def toDict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for f in fields(self):  # type: ignore[arg-type]
            value = getattr(self, f.name)
            result[f.name] = BaseDTO._serialize(value)
        return result

    @staticmethod
    def _serialize(value: Any) -> Any:
        if isinstance(value, BaseDTO):
            return value.toDict()
        if isinstance(value, list):
            return [BaseDTO._serialize(v) for v in value]
        if isinstance(value, date):
            return value.isoformat()
        return value