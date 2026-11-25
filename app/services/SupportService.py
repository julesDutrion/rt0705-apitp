from typing import List
from urllib.parse import urlparse

from pymongo.errors import DuplicateKeyError

from ..dao import FilmDAO, SupportDAO, SupportTypeDAO
from ..Exceptions import (
    AlreadyExistsError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
)
from ..models import SupportDTO, SupportTypeDTO


class SupportService:
    def __init__(
        self,
        supportDAO: SupportDAO,
        filmDAO: FilmDAO,
        supportTypeDAO: SupportTypeDAO,
    ) -> None:
        self._supportDAO = supportDAO
        self._filmDAO = filmDAO
        self._supportTypeDAO = supportTypeDAO

    def getAllSupports(self) -> List[SupportDTO]:
        return self._supportDAO.getAll()

    def getSupportById(self, idSupport: int) -> SupportDTO:
        support = self._supportDAO.getById(idSupport)
        if support is None:
            raise NotFoundError(f"Support {idSupport} not found")
        return support

    def getSupportsByFilmId(self, idFilm: str) -> List[SupportDTO]:
        if not self._filmDAO.existsFilm(idFilm):
            raise NotFoundError(f"Film {idFilm} not found")
        return self._supportDAO.getByFilmId(idFilm)

    def createSupport(self, support: SupportDTO) -> SupportDTO:
        support.supportType = self._checkReferences(support)
        try:
            return self._supportDAO.create(support)
        except DuplicateKeyError:
            raise AlreadyExistsError(
                f"Support {support.idSupport} already exists"
            )

    def updateSupport(self, support: SupportDTO) -> SupportDTO:
        support.supportType = self._checkReferences(support)
        if not self._supportDAO.update(support):
            raise NotFoundError(f"Support {support.idSupport} not found")
        return support

    def deleteSupport(self, idSupport: int) -> None:
        if not self._supportDAO.delete(idSupport):
            raise NotFoundError(f"Support {idSupport} not found")

    def _checkReferences(self, support: SupportDTO) -> SupportTypeDTO:
        if not isinstance(support.idFilm, str) or not support.idFilm.strip():
            raise InvalidRequestError("idFilm must be a non-empty string")
        if not isinstance(support.idSupportType, int) or isinstance(
            support.idSupportType, bool
        ):
            raise InvalidRequestError("idSupportType must be an integer")
        if not self._filmDAO.existsFilm(support.idFilm):
            raise InvalidReferenceError(f"Film {support.idFilm} does not exist")

        supportType = self._supportTypeDAO.getById(support.idSupportType)
        if supportType is None:
            raise InvalidReferenceError(
                f"Support type {support.idSupportType} does not exist"
            )

        if supportType.mode == "physical":
            if not isinstance(support.location, str) or not support.location.strip():
                raise InvalidRequestError(
                    "location is required for a physical support"
                )
            if support.url is not None:
                raise InvalidRequestError(
                    "url is not allowed for a physical support"
                )
        elif supportType.mode == "digital":
            if not isinstance(support.url, str) or not support.url.strip():
                raise InvalidRequestError("url is required for a digital support")
            if support.location is not None:
                raise InvalidRequestError(
                    "location is not allowed for a digital support"
                )
            try:
                parsedUrl = urlparse(support.url)
            except ValueError:
                raise InvalidRequestError(
                    "url must be a valid HTTP or HTTPS URL"
                )
            if (
                parsedUrl.scheme not in {"http", "https"}
                or not parsedUrl.hostname
            ):
                raise InvalidRequestError(
                    "url must be a valid HTTP or HTTPS URL"
                )
        else:
            raise InvalidRequestError(
                f"Unsupported mode '{supportType.mode}' for support type"
            )
        return supportType
