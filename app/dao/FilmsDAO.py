"""DAO d'accès aux films (MongoDB / pymongo).

En base, un film ne contient que les IDENTIFIANTS de ses objets liés.
À la lecture, le DAO recharge ces objets depuis leurs collections et
construit des FilmDTO complets (hydratation).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Type

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database


from ..models.LanguageDTO import LanguageDTO
from ..models.ActorDTO import ActorDTO
from ..models.BaseDTO import BaseDTO
from ..models.ClassificationDTO import ClassificationDTO
from ..models.DirectorDTO import DirectorDTO
from ..models.FilmDTO import FilmDTO
from ..models.GenreDTO import GenreDTO
from ..models.SupportDTO import SupportDTO

# On n'expose jamais l'_id interne de MongoDB : l'identifiant métier est idFilm.
_NO_MONGO_ID: Dict[str, int] = {"_id": 0}


class FilmDAO:
    """Accès aux données de la collection `films`.

    Document stocké :
        idFilm, title, synopsis, releaseDate, duration, posterUrl, addedDate,
        idDirector, idClassification, idSupport, idNativeLanguage,
        idLanguages[], idGenres[], idActors[]

    Les entités liées doivent déjà exister dans leurs collections
    (directors, classifications, supports, languages, genres, actors).
    """

    FILMS = "films"
    DIRECTORS = "directors"
    CLASSIFICATIONS = "classifications"
    SUPPORTS = "supports"
    LANGUAGES = "languages"
    GENRES = "genres"
    ACTORS = "actors"

    def __init__(self, database: Database) -> None:
        self._database: Database = database
        self._films: Collection = database[self.FILMS]
        self._films.create_index([("idFilm", ASCENDING)], unique=True)
        self._films.create_index([("title", ASCENDING)])

    # ------------------------------------------------------------------ #
    # Lecture
    # ------------------------------------------------------------------ #
    def getAllFilms(self) -> List[FilmDTO]:
        return self._findFilms({})

    def getFilmById(self, idFilm: str) -> Optional[FilmDTO]:
        document = self._films.find_one({"idFilm": idFilm}, _NO_MONGO_ID)
        if document is None:
            return None
        return self._hydrate([document])[0]

    def searchFilms(
        self,
        filters: Dict[str, Any],
        allowedClassificationIds: Optional[List[int]] = None
    ) -> List[FilmDTO]:
        """
        Recherche des films avec plusieurs filtres cumulables.

        Les filtres sont combinés avec une logique ET.

        allowedClassificationIds :
            None = aucune restriction de classification.
            []   = aucune classification autorisée.
            [1, 2] = uniquement les classifications 1 et 2.
        """
        query: Dict[str, Any] = {}

        # Recherche partielle sur le titre, insensible à la casse.
        title = filters.get("title")
        if title:
            query["title"] = {
                "$regex": re.escape(title),
                "$options": "i"
            }

        # Correspondance avec les identifiants des entités liées.
        filterMapping = {
            "genre": "idGenres",
            "director": "idDirector",
            "actor": "idActors",
            "language": "idLanguages"
        }

        for filterName, databaseField in filterMapping.items():
            value = filters.get(filterName)

            if value is not None:
                query[databaseField] = value

        # Restriction des classifications autorisées pour le compte.
        if allowedClassificationIds is not None:
            query["idClassification"] = {
                "$in": allowedClassificationIds
            }

        return self._findFilms(query)

    def existsFilm(self, idFilm: str) -> bool:
        return self._films.count_documents(
            {"idFilm": idFilm}, limit=1
        ) > 0

    # ------------------------------------------------------------------ #
    # Écriture
    # ------------------------------------------------------------------ #
    def createFilm(self, film: FilmDTO) -> FilmDTO:
        """Insère un film (ids uniquement). Lève DuplicateKeyError si idFilm existe."""
        self._films.insert_one(self._toDocument(film))
        return film

    def updateFilm(self, film: FilmDTO) -> bool:
        """Remplace le film ayant le même idFilm. Retourne False s'il n'existe pas."""
        result = self._films.replace_one(
            {"idFilm": film.idFilm}, self._toDocument(film)
        )
        return result.matched_count == 1

    def deleteFilm(self, idFilm: str) -> bool:
        """Supprime un film. Retourne False s'il n'existe pas."""
        result = self._films.delete_one({"idFilm": idFilm})
        return result.deleted_count == 1

    # ------------------------------------------------------------------ #
    # Interne : FilmDTO -> document (ids uniquement)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _toDocument(film: FilmDTO) -> Dict[str, Any]:
        return {
            "idFilm": film.idFilm,
            "title": film.title,
            "synopsis": film.synopsis,
            "releaseDate": film.releaseDate.isoformat(),
            "duration": film.duration,
            "posterUrl": film.posterUrl,
            "addedDate": film.addedDate.isoformat(),
            "idDirector": film.director.idDirector if film.director else None,
            "idClassification": (
                film.classification.idClassification if film.classification else None
            ),
            "idSupport": film.support.idSupport if film.support else None,
            "idNativeLanguage": (
                film.nativeLanguage.idLanguage if film.nativeLanguage else None
            ),
            "idLanguages": [language.idLanguage for language in film.languages],
            "idGenres": [genre.idGenre for genre in film.genre],
            "idActors": [actor.idActor for actor in film.actors],
        }

    # ------------------------------------------------------------------ #
    # Interne : documents -> FilmDTO complets (hydratation)
    # ------------------------------------------------------------------ #
    def _findFilms(self, query: Dict[str, Any]) -> List[FilmDTO]:
        documents = list(
            self._films.find(query, _NO_MONGO_ID).sort("title", ASCENDING)
        )
        return self._hydrate(documents)

    def _hydrate(self, documents: List[Dict[str, Any]]) -> List[FilmDTO]:
        """Charge en une seule requête par collection tous les objets liés."""
        directors = self._loadByIds(
            self.DIRECTORS, "idDirector", DirectorDTO,
            (d.get("idDirector") for d in documents),
        )
        classifications = self._loadByIds(
            self.CLASSIFICATIONS, "idClassification", ClassificationDTO,
            (d.get("idClassification") for d in documents),
        )
        supports = self._loadByIds(
            self.SUPPORTS, "idSupport", SupportDTO,
            (d.get("idSupport") for d in documents),
        )
        languages = self._loadByIds(
            self.LANGUAGES, "idLanguage", LanguageDTO,
            self._flatten(
                documents, "idLanguages", extra=[d.get("idNativeLanguage") for d in documents]
            ),
        )
        genres = self._loadByIds(
            self.GENRES, "idGenre", GenreDTO, self._flatten(documents, "idGenres")
        )
        actors = self._loadByIds(
            self.ACTORS, "idActor", ActorDTO, self._flatten(documents, "idActors")
        )

        films: List[FilmDTO] = []
        for doc in documents:
            films.append(
                FilmDTO(
                    idFilm=doc["idFilm"],
                    title=doc["title"],
                    synopsis=doc["synopsis"],
                    releaseDate=self._toDate(doc["releaseDate"]),
                    duration=doc["duration"],
                    posterUrl=doc["posterUrl"],
                    addedDate=self._toDate(doc["addedDate"]),
                    director=directors.get(doc.get("idDirector")),
                    classification=classifications.get(doc.get("idClassification")),
                    support=supports.get(doc.get("idSupport")),
                    nativeLanguage=languages.get(doc.get("idNativeLanguage")),
                    languages=[
                        languages[i] for i in doc.get("idLanguages", []) if i in languages
                    ],
                    genre=[genres[i] for i in doc.get("idGenres", []) if i in genres],
                    actors=[actors[i] for i in doc.get("idActors", []) if i in actors],
                )
            )
        return films

    def _loadByIds(
        self,
        collectionName: str,
        idField: str,
        dtoClass: Type[BaseDTO],
        ids: Iterable[Any],
    ) -> Dict[Any, Any]:
        """Retourne {id: DTO} pour les ids demandés (les ids None sont ignorés)."""
        uniqueIds = {i for i in ids if i is not None}
        if not uniqueIds:
            return {}
        cursor = self._database[collectionName].find(
            {idField: {"$in": list(uniqueIds)}}, _NO_MONGO_ID
        )
        return {doc[idField]: dtoClass.fromDict(doc) for doc in cursor}  # type: ignore[attr-defined]

    @staticmethod
    def _flatten(
        documents: List[Dict[str, Any]], key: str, extra: Optional[List[Any]] = None
    ) -> List[Any]:
        values: List[Any] = list(extra) if extra else []
        for doc in documents:
            values.extend(doc.get(key, []))
        return values

    @staticmethod
    def _toDate(value: Any) -> date:
        return value if isinstance(value, date) else date.fromisoformat(value)