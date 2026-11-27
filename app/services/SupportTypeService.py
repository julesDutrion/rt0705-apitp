from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import SupportDAO, SupportTypeDAO
from ..Exceptions import (
    AlreadyExistsError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
)
from ..models import SupportTypeDTO
from ._input import dtoFromInput


class SupportTypeService:
    """Classe qui représente le service de gestion des types de supports."""

    MODES = frozenset({"physical", "digital"})

    def __init__(
        self, supportTypeDAO: SupportTypeDAO, supportDAO: SupportDAO
    ) -> None:
        self._supportTypeDAO = supportTypeDAO
        self._supportDAO = supportDAO

    def getAllSupportTypes(self) -> List[SupportTypeDTO]:
        """
        Méthode qui récupère tous les types de supports.

        :return: Liste des DTO de types de supports.
        """
        return self._supportTypeDAO.getAll()

    def getSupportTypeById(self, idSupportType: int) -> SupportTypeDTO:
        """
        Méthode qui récupère un type de support par son identifiant.

        :param idSupportType: Identifiant du type de support.
        :return: DTO du type de support.
        :raises NotFoundError: Si le type de support n'existe pas.
        """
        supportType = self._supportTypeDAO.getById(idSupportType)
        if supportType is None:
            raise NotFoundError(f"Support type {idSupportType} not found")
        return supportType

    def createSupportType(self, data: Any) -> SupportTypeDTO:
        """
        Méthode qui crée un type de support.

        :param data: Données du type de support.
        :return: DTO du type créé.
        :raises InvalidRequestError: Si le nom ou le mode est invalide.
        :raises AlreadyExistsError: Si l'identifiant existe déjà.
        """
        supportType = dtoFromInput(data, SupportTypeDTO.fromDictWithoutId)
        self._validate(supportType)
        try:
            return self._supportTypeDAO.create(supportType)
        except DuplicateKeyError:
            raise AlreadyExistsError(
                f"Support type {supportType.idSupportType} already exists"
            )

    def updateSupportType(self, idSupportType: int, data: Any) -> SupportTypeDTO:
        """
        Méthode qui remplace les données d'un type de support.

        :param idSupportType: Identifiant du type à modifier.
        :param data: Nouvelles données du type de support.
        :return: DTO du type modifié.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises NotFoundError: Si le type de support n'existe pas.
        :raises ConflictError: Si son mode change alors qu'il est utilisé.
        """
        if (
            isinstance(data, dict)
            and "idSupportType" in data
            and data["idSupportType"] != idSupportType
        ):
            raise InvalidRequestError(
                "idSupportType in the URL and in the body must match"
            )
        supportType = dtoFromInput(data, SupportTypeDTO.fromDictWithoutId)
        supportType.idSupportType = idSupportType
        self._validate(supportType)
        current = self.getSupportTypeById(supportType.idSupportType)
        if current.mode != supportType.mode and self._supportDAO.existsForType(
            supportType.idSupportType
        ):
            raise ConflictError(
                "Cannot change the mode of a support type that has supports"
            )
        if not self._supportTypeDAO.update(supportType):
            raise NotFoundError(
                f"Support type {supportType.idSupportType} not found"
            )
        return supportType

    def deleteSupportType(self, idSupportType: int) -> None:
        """
        Méthode qui supprime un type de support non utilisé.

        :param idSupportType: Identifiant du type à supprimer.
        :raises NotFoundError: Si le type de support n'existe pas.
        :raises ConflictError: Si le type est utilisé par un support.
        """
        self.getSupportTypeById(idSupportType)
        if self._supportDAO.existsForType(idSupportType):
            raise ConflictError(
                f"Support type {idSupportType} is used by existing supports"
            )
        if not self._supportTypeDAO.delete(idSupportType):
            raise NotFoundError(f"Support type {idSupportType} not found")

    @classmethod
    def _validate(cls, supportType: SupportTypeDTO) -> None:
        if not isinstance(supportType.name, str) or not supportType.name.strip():
            raise InvalidRequestError("name must be a non-empty string")
        if not isinstance(supportType.mode, str) or supportType.mode not in cls.MODES:
            raise InvalidRequestError("mode must be 'physical' or 'digital'")
