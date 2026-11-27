from typing import Dict, Iterable, List, Optional, Set

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from ..models import SupportDTO, SupportTypeDTO


_NO_MONGO_ID = {"_id": 0}


class SupportDAO:
    COLLECTION_NAME = "supports"

    def __init__(self, database: Database) -> None:
        self._database = database
        self._collection = database[self.COLLECTION_NAME]
        self._collection.create_index([("idSupport", ASCENDING)], unique=True)
        self._collection.create_index([("idFilm", ASCENDING)])
        self._collection.create_index([("idSupportType", ASCENDING)])

    def getAll(self) -> List[SupportDTO]:
        documents = self._collection.find({}, _NO_MONGO_ID).sort(
            "idSupport", ASCENDING
        )
        return self._hydrate(list(documents))

    def getById(self, idSupport: int) -> Optional[SupportDTO]:
        document = self._collection.find_one(
            {"idSupport": idSupport}, _NO_MONGO_ID
        )
        return self._hydrate([document])[0] if document else None

    def getByIds(self, idSupports: Iterable[int]) -> List[SupportDTO]:
        supportIds = set(idSupports)
        if not supportIds:
            return []
        documents = self._collection.find(
            {"idSupport": {"$in": list(supportIds)}}, _NO_MONGO_ID
        ).sort("idSupport", ASCENDING)
        return self._hydrate(list(documents))

    def getByFilmId(self, idFilm: str) -> List[SupportDTO]:
        documents = self._collection.find(
            {"idFilm": idFilm}, _NO_MONGO_ID
        ).sort("idSupport", ASCENDING)
        return self._hydrate(list(documents))

    def getFilmIdsBySupportType(self, idSupportType: int) -> List[str]:
        return self._collection.distinct(
            "idFilm", {"idSupportType": idSupportType}
        )

    def getByFilmIds(self, idFilms: Iterable[str]) -> Dict[str, List[SupportDTO]]:
        filmIds: Set[str] = set(idFilms)
        if not filmIds:
            return {}
        documents = list(
            self._collection.find(
                {"idFilm": {"$in": list(filmIds)}}, _NO_MONGO_ID
            ).sort("idSupport", ASCENDING)
        )
        supportsByFilm: Dict[str, List[SupportDTO]] = {
            idFilm: [] for idFilm in filmIds
        }
        for support in self._hydrate(documents):
            supportsByFilm.setdefault(support.idFilm, []).append(support)
        return supportsByFilm

    def exists(self, idSupport: int) -> bool:
        return self._collection.count_documents(
            {"idSupport": idSupport}, limit=1
        ) > 0

    def existsForFilm(self, idFilm: str) -> bool:
        return self._collection.count_documents({"idFilm": idFilm}, limit=1) > 0

    def existsForType(self, idSupportType: int) -> bool:
        return self._collection.count_documents(
            {"idSupportType": idSupportType}, limit=1
        ) > 0

    def create(self, support: SupportDTO) -> SupportDTO:
        if support.idSupport is None:
            latest = self._collection.find_one(
                {}, {"idSupport": 1, "_id": 0},
                sort=[("idSupport", DESCENDING)],
            )
            support.idSupport = latest["idSupport"] + 1 if latest else 1
        self._collection.insert_one(self._toDocument(support))
        return support

    def update(self, support: SupportDTO) -> bool:
        result = self._collection.replace_one(
            {"idSupport": support.idSupport}, self._toDocument(support)
        )
        return result.matched_count == 1

    def delete(self, idSupport: int) -> bool:
        result = self._collection.delete_one({"idSupport": idSupport})
        return result.deleted_count == 1

    @staticmethod
    def _toDocument(support: SupportDTO) -> Dict[str, object]:
        return {
            "idSupport": support.idSupport,
            "idFilm": support.idFilm,
            "idSupportType": support.idSupportType,
            "location": support.location,
            "url": support.url,
        }

    def _hydrate(self, documents: List[Dict[str, object]]) -> List[SupportDTO]:
        typeIds = {
            document["idSupportType"]
            for document in documents
            if document.get("idSupportType") is not None
        }
        types: Dict[int, SupportTypeDTO] = {}
        if typeIds:
            typeDocuments = self._database["supportTypes"].find(
                {"idSupportType": {"$in": list(typeIds)}}, _NO_MONGO_ID
            )
            types = {
                document["idSupportType"]: SupportTypeDTO.fromDict(document)
                for document in typeDocuments
            }

        return [
            SupportDTO(
                idSupport=document["idSupport"],
                idFilm=document["idFilm"],
                idSupportType=document["idSupportType"],
                location=document.get("location"),
                url=document.get("url"),
                supportType=types.get(document["idSupportType"]),
            )
            for document in documents
        ]
