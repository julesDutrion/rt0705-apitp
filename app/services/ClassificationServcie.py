from typing import List

from pymongo.errors import DuplicateKeyError

from dao import ClassificationDAO
from ..Exceptions import AlreadyExistsError, NotFoundError
from ..models.ClassificationDTO import ClassificationDTO


class ClassificationService:
    def __init__(self, classificationDAO: ClassificationDAO) -> None:
        self._classificationDAO = classificationDAO

    def getAllClassifications(self) -> List[ClassificationDTO]:
        return self._classificationDAO.getAll()

    def getClassificationsByMinAge(self, minAge: int) -> List[ClassificationDTO]:
        return self._classificationDAO.getByMinAge(minAge)

    def getClassificationById(self, idClassification: int) -> ClassificationDTO:
        classification = self._classificationDAO.getById(idClassification)
        if classification is None:
            raise NotFoundError(f"Classification {idClassification} not found")
        return classification

    def createClassification(self, classification: ClassificationDTO) -> ClassificationDTO:
        try:
            return self._classificationDAO.create(classification)
        except DuplicateKeyError:
            raise AlreadyExistsError(
                f"Classification {classification.idClassification} already exists"
            )