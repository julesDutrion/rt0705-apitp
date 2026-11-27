"""DAO d'accès aux films (MongoDB / pymongo).

En base, un film ne contient que les IDENTIFIANTS de ses objets liés.
À la lecture, le DAO recharge ces objets depuis leurs collections et
construit des FilmDTO complets (hydratation).
"""

from __future__ import annotations

import re
import uuid
import logging
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Type

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database


from ..models import (
    ActorDTO,
    BaseDTO,
    ClassificationDTO,
    DirectorDTO,
    FilmDTO,
    GenreDTO,
    LanguageDTO,
)

# On n'expose jamais l'_id interne de MongoDB : l'identifiant métier est idFilm.
_NO_MONGO_ID: Dict[str, int] = {"_id": 0}
_LOGGER = logging.getLogger(__name__)


class FilmDAO:
    """Classe qui représente l'accès aux données des films."""

    FILMS = "films"
    DIRECTORS = "directors"
    CLASSIFICATIONS = "classifications"
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
        """
        Méthode qui récupère tous les films.

        :return: Liste des DTO de films.
        """
        return self._findFilms({})

    def getFilmById(self, idFilm: str) -> Optional[FilmDTO]:
        """
        Méthode qui récupère un film par son identifiant.

        :param idFilm: Identifiant du film.
        :return: DTO du film ou None s'il est absent.
        """
        document = self._films.find_one({"idFilm": idFilm}, _NO_MONGO_ID)
        if document is None:
            return None
        return self._hydrate([document])[0]

    def searchFilms(
        self,
        filters: Dict[str, Any],
        allowedClassificationIds: Optional[List[int]] = None,
        supportFilmIds: Optional[List[str]] = None,
    ) -> List[FilmDTO]:
        """
        Méthode qui recherche les films selon plusieurs critères.

        :param filters: Critères de recherche.
        :param allowedClassificationIds: Classifications autorisées ou None.
        :param supportFilmIds: Films associés au type recherché ou None.
        :return: Liste des DTO de films correspondants.
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

        if supportFilmIds is not None:
            query["idFilm"] = {"$in": supportFilmIds}

        return self._findFilms(query)

    def existsFilm(self, idFilm: str) -> bool:
        """
        Méthode qui vérifie l'existence d'un film.

        :param idFilm: Identifiant du film.
        :return: True si le film existe, sinon False.
        """
        return self._films.count_documents(
            {"idFilm": idFilm}, limit=1
        ) > 0

    # ------------------------------------------------------------------ #
    # Écriture
    # ------------------------------------------------------------------ #
    def createFilm(self, film: FilmDTO) -> FilmDTO:
        """
        Méthode qui enregistre un film.

        :param film: DTO du film à enregistrer.
        :return: DTO du film enregistré.
        :raises DuplicateKeyError: Si l'identifiant existe déjà.
        """
        if film.idFilm is None:
            while True:
                candidate = str(uuid.uuid4())
                if not self.existsFilm(candidate):
                    film.idFilm = candidate
                    break
        self._films.insert_one(self._toDocument(film))
        return film

    def updateFilm(self, film: FilmDTO) -> bool:
        """
        Méthode qui remplace les données d'un film.

        :param film: DTO contenant les données modifiées.
        :return: True si un film a été modifié, sinon False.
        """
        result = self._films.replace_one(
            {"idFilm": film.idFilm}, self._toDocument(film)
        )
        return result.matched_count == 1

    def deleteFilm(self, idFilm: str) -> bool:
        """
        Méthode qui supprime un film.

        :param idFilm: Identifiant du film.
        :return: True si un film a été supprimé, sinon False.
        """
        result = self._films.delete_one({"idFilm": idFilm})
        return result.deleted_count == 1

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
            "idNativeLanguage": (
                film.nativeLanguage.idLanguage if film.nativeLanguage else None
            ),
            "idLanguages": [language.idLanguage for language in film.languages],
            "idGenres": [genre.idGenre for genre in film.genre],
            "idActors": [actor.idActor for actor in film.actors],
        }

    def _findFilms(self, query: Dict[str, Any]) -> List[FilmDTO]:
        documents = list(
            self._films.find(query, _NO_MONGO_ID).sort("title", ASCENDING)
        )
        return self._hydrate(documents)

    def _hydrate(self, documents: List[Dict[str, Any]]) -> List[FilmDTO]:
        directors = self._loadByIds(
            self.DIRECTORS, "idDirector", DirectorDTO,
            (d.get("idDirector") for d in documents),
        )
        classifications = self._loadClassifications(
            d.get("idClassification") for d in documents
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
            idClassification = doc.get("idClassification")
            classification = (
                classifications.get(idClassification)
                if type(idClassification) is int
                else None
            )
            if (
                idClassification is not None
                and (
                    type(idClassification) is not int
                    or idClassification not in classifications
                )
            ):
                _LOGGER.warning(
                    "Film %s references a missing or invalid classification %r",
                    doc.get("idFilm"),
                    idClassification,
                )
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
                    classification=classification,
                    nativeLanguage=languages.get(doc.get("idNativeLanguage")),
                    languages=[
                        languages[i] for i in doc.get("idLanguages", []) if i in languages
                    ],
                    genre=[genres[i] for i in doc.get("idGenres", []) if i in genres],
                    actors=[actors[i] for i in doc.get("idActors", []) if i in actors],
                )
            )
        return films

    def _loadClassifications(
        self, ids: Iterable[Any]
    ) -> Dict[Any, ClassificationDTO]:
        uniqueIds = {
            idClassification
            for idClassification in ids
            if type(idClassification) is int and idClassification > 0
        }
        if not uniqueIds:
            return {}

        documents = self._database[self.CLASSIFICATIONS].find(
            {"idClassification": {"$in": list(uniqueIds)}},
            _NO_MONGO_ID,
        )
        classifications: Dict[Any, ClassificationDTO] = {}
        for document in documents:
            idClassification = document.get("idClassification")
            minAge = document.get("minAge")
            if (
                type(idClassification) is not int
                or idClassification < 1
                or type(minAge) is not int
                or minAge < 0
            ):
                _LOGGER.warning(
                    "Ignoring invalid classification record %r",
                    idClassification,
                )
                continue
            classifications[idClassification] = ClassificationDTO.fromDict(
                document
            )
        return classifications

    def _loadByIds(
        self,
        collectionName: str,
        idField: str,
        dtoClass: Type[BaseDTO],
        ids: Iterable[Any],
    ) -> Dict[Any, Any]:
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