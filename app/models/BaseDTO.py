"""DTOs du package Model (vidéothèque).

Les noms d'attributs suivent le diagramme de classes (camelCase) afin que
les clés JSON de l'API correspondent exactement au modèle.
"""

from __future__ import annotations

from dataclasses import fields
from datetime import date
from typing import Any, Dict, List, Optional
class BaseDTO:
    """Classe qui représente le socle commun des objets de transfert de données."""

    ID_FIELDS = frozenset()

    def toDict(self) -> Dict[str, Any]:
        """
        Méthode qui convertit le DTO en dictionnaire.

        :return: Dictionnaire contenant les champs du DTO.
        """
        result: Dict[str, Any] = {}
        for f in fields(self):  # type: ignore[arg-type]
            value = getattr(self, f.name)
            result[f.name] = BaseDTO._serialize(value)
        return result

    def toDictWithoutId(self) -> Dict[str, Any]:
        """
        Méthode qui convertit le DTO en dictionnaire sans ses identifiants.

        :return: Dictionnaire des champs non identifiants du DTO.
        """
        result = self.toDict()
        for idField in self.ID_FIELDS:
            result.pop(idField, None)
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