from typing import Any, Dict, List
from urllib.parse import urlparse

from pymongo.errors import DuplicateKeyError

from ..dao import FilmDAO, LoanDAO, SupportDAO, SupportTypeDAO
from ..Exceptions import (
    AlreadyExistsError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
)
from ..models import SupportDTO, SupportTypeDTO
from ._input import dtoFromInput


class SupportService:
    """Classe qui représente le service de gestion des supports."""

    def __init__(
        self,
        supportDAO: SupportDAO,
        filmDAO: FilmDAO,
        supportTypeDAO: SupportTypeDAO,
        loanDAO: LoanDAO,
    ) -> None:
        self._supportDAO = supportDAO
        self._filmDAO = filmDAO
        self._supportTypeDAO = supportTypeDAO
        self._loanDAO = loanDAO

    def toPublicDict(self, support: SupportDTO) -> Dict[str, Any]:
        """
        Méthode qui prépare les données publiques d'un support.

        :param support: DTO du support.
        :return: Données du support incluant sa disponibilité.
        """
        return self.toPublicDicts([support])[0]

    def toPublicDicts(
        self, supports: List[SupportDTO]
    ) -> List[Dict[str, Any]]:
        """
        Méthode qui prépare les données publiques de plusieurs supports.

        :param supports: Supports à convertir.
        :return: Liste des données publiques des supports.
        """
        if not supports:
            return []
        borrowedSupportIds = self._loanDAO.getActivePhysicalSupportIds()
        supportDicts = []
        for support in supports:
            data = support.toDict()
            isPhysical = (
                support.supportType is not None
                and support.supportType.mode == "physical"
            )
            data["isAvailable"] = (
                support.idSupport not in borrowedSupportIds
                if isPhysical
                else None
            )
            supportDicts.append(data)
        return supportDicts

    def getAllSupports(self) -> List[SupportDTO]:
        """
        Méthode qui récupère tous les supports.

        :return: Liste des DTO de supports.
        """
        return self._supportDAO.getAll()

    def getSupportById(self, idSupport: int) -> SupportDTO:
        """
        Méthode qui récupère un support par son identifiant.

        :param idSupport: Identifiant du support.
        :return: DTO du support.
        :raises NotFoundError: Si le support n'existe pas.
        """
        support = self._supportDAO.getById(idSupport)
        if support is None:
            raise NotFoundError(f"Support {idSupport} not found")
        return support

    def getSupportsByFilmId(self, idFilm: str) -> List[SupportDTO]:
        """
        Méthode qui récupère les supports associés à un film.

        :param idFilm: Identifiant du film.
        :return: Liste des DTO de supports du film.
        :raises NotFoundError: Si le film n'existe pas.
        """
        if not self._filmDAO.existsFilm(idFilm):
            raise NotFoundError(f"Film {idFilm} not found")
        return self._supportDAO.getByFilmId(idFilm)

    def createSupport(self, data: Any) -> SupportDTO:
        """
        Méthode qui crée un support associé à un film et à un type.

        :param data: Données du support.
        :return: DTO du support créé.
        :raises InvalidRequestError: Si les données du support sont invalides.
        :raises InvalidReferenceError: Si le film ou le type est absent.
        :raises AlreadyExistsError: Si l'identifiant du support existe déjà.
        """
        support = dtoFromInput(data, SupportDTO.fromDictWithoutId)
        support.supportType = self._checkReferences(support)
        try:
            return self._supportDAO.create(support)
        except DuplicateKeyError:
            raise AlreadyExistsError(
                f"Support {support.idSupport} already exists"
            )

    def updateSupport(self, idSupport: int, data: Any) -> SupportDTO:
        """
        Méthode qui remplace les données d'un support.

        :param idSupport: Identifiant du support à modifier.
        :param data: Nouvelles données du support.
        :return: DTO du support modifié.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises InvalidReferenceError: Si le film ou le type est absent.
        :raises NotFoundError: Si le support n'existe pas.
        """
        if (
            isinstance(data, dict)
            and "idSupport" in data
            and data["idSupport"] != idSupport
        ):
            raise InvalidRequestError(
                "idSupport in the URL and in the body must match"
            )
        support = dtoFromInput(data, SupportDTO.fromDictWithoutId)
        support.idSupport = idSupport
        support.supportType = self._checkReferences(support)
        if not self._supportDAO.update(support):
            raise NotFoundError(f"Support {support.idSupport} not found")
        return support

    def deleteSupport(self, idSupport: int) -> None:
        """
        Méthode qui supprime un support.

        :param idSupport: Identifiant du support à supprimer.
        :raises NotFoundError: Si le support n'existe pas.
        """
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
