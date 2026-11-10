"""DTOs du package Model (vidéothèque).

Les noms d'attributs suivent le diagramme de classes (camelCase) afin que
les clés JSON de l'API correspondent exactement au modèle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date
from typing import Any, Dict, List, Optional
from .BaseDTO import BaseDTO
from .DirectorDTO import DirectorDTO
from .ClassificationDTO import ClassificationDTO
from .SupportDTO import SupportDTO
from .GenreDTO import GenreDTO
from .ActorDTO import ActorDTO
from .LanguageDTO import LanguageDTO


@dataclass
class FilmDTO(BaseDTO):
    idFilm: str
    title: str
    synopsis: str
    releaseDate: date
    duration: int
    posterUrl: str
    addedDate: date

    # Associations du diagramme
    director: Optional[DirectorDTO] = None            # 1
    classification: Optional[ClassificationDTO] = None  # 1
    support: Optional[SupportDTO] = None              # 1
    nativeLanguage: Optional[LanguageDTO] = None       # 1
    languages: List[LanguageDTO] = field(default_factory=list)  # *
    genre: List[GenreDTO] = field(default_factory=list)        # *
    actors: List[ActorDTO] = field(default_factory=list)       # *

    @classmethod
    def fromDict(cls, data: Dict[str, Any]) -> "FilmDTO":
        def _date(value: Any) -> date:
            return value if isinstance(value, date) else date.fromisoformat(value)

        def _one(key: str, dto: Any) -> Any:
            return dto.fromDict(data[key]) if data.get(key) else None

        return cls(
            idFilm=data["idFilm"],
            title=data["title"],
            synopsis=data["synopsis"],
            releaseDate=_date(data["releaseDate"]),
            duration=data["duration"],
            posterUrl=data["posterUrl"],
            addedDate=_date(data["addedDate"]),
            director=_one("director", DirectorDTO),
            classification=_one("classification", ClassificationDTO),
            support=_one("support", SupportDTO),
            nativeLanguage=_one("nativeLanguage", LanguageDTO),
            languages=[LanguageDTO.fromDict(x) for x in data.get("languages", [])],
            genre=[GenreDTO.fromDict(x) for x in data.get("genre", [])],
            actors=[ActorDTO.fromDict(x) for x in data.get("actors", [])],
        )
