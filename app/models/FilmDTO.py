"""DTOs du package Model (vidéothèque).

Les noms d'attributs suivent le diagramme de classes (camelCase) afin que
les clés JSON de l'API correspondent exactement au modèle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
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
    title: str
    synopsis: str
    releaseDate: date
    duration: int
    posterUrl: str
    addedDate: date
    idFilm: Optional[str] = None
    ID_FIELDS = frozenset({"idFilm"})

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

        def _one(key: str, dto: Any, idField: str) -> Any:
            value = data.get(key)
            if not value:
                return None
            if isinstance(value, dict) and idField in value and len(value) == 1:
                placeholders = {
                    f.name: None
                    for f in fields(dto)
                    if f.name != idField
                }
                return dto(**{idField: value[idField]}, **placeholders)
            return dto.fromDict(value)

        def _many(dto: Any, idField: str, value: Any) -> Any:
            if isinstance(value, dict) and idField in value and len(value) == 1:
                placeholders = {
                    f.name: None
                    for f in fields(dto)
                    if f.name != idField
                }
                return dto(**{idField: value[idField]}, **placeholders)
            return dto.fromDict(value)

        return cls(
            idFilm=data.get("idFilm"),
            title=data["title"],
            synopsis=data["synopsis"],
            releaseDate=_date(data["releaseDate"]),
            duration=data["duration"],
            posterUrl=data["posterUrl"],
            addedDate=_date(data["addedDate"]),
            director=_one("director", DirectorDTO, "idDirector"),
            classification=_one("classification", ClassificationDTO, "idClassification"),
            support=_one("support", SupportDTO, "idSupport"),
            nativeLanguage=_one("nativeLanguage", LanguageDTO, "idLanguage"),
            languages=[
                _many(LanguageDTO, "idLanguage", x)
                for x in data.get("languages", [])
            ],
            genre=[
                _many(GenreDTO, "idGenre", x)
                for x in data.get("genre", [])
            ],
            actors=[
                _many(ActorDTO, "idActor", x)
                for x in data.get("actors", [])
            ],
        )

    @classmethod
    def fromDictWithoutId(cls, data: Dict[str, Any]) -> "FilmDTO":
        dataWithoutId = dict(data)
        dataWithoutId.pop("idFilm", None)
        return cls.fromDict(dataWithoutId)
