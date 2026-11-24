from typing import List

from pymongo.errors import DuplicateKeyError

from ..dao import SupportDAO, SupportTypeDAO
from ..Exceptions import (
    AlreadyExistsError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
)
from ..models import SupportTypeDTO


class SupportTypeService:
    MODES = frozenset({"physical", "digital"})

    def __init__(
        self, supportTypeDAO: SupportTypeDAO, supportDAO: SupportDAO
    ) -> None:
        self._supportTypeDAO = supportTypeDAO
        self._supportDAO = supportDAO

    def getAllSupportTypes(self) -> List[SupportTypeDTO]:
        return self._supportTypeDAO.getAll()

    def getSupportTypeById(self, idSupportType: int) -> SupportTypeDTO:
        supportType = self._supportTypeDAO.getById(idSupportType)
        if supportType is None:
            raise NotFoundError(f"Support type {idSupportType} not found")
        return supportType

    def createSupportType(self, supportType: SupportTypeDTO) -> SupportTypeDTO:
        self._validate(supportType)
        try:
            return self._supportTypeDAO.create(supportType)
        except DuplicateKeyError:
            raise AlreadyExistsError(
                f"Support type {supportType.idSupportType} already exists"
            )

    def updateSupportType(self, supportType: SupportTypeDTO) -> SupportTypeDTO:
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
