from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import ClassificationDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import ClassificationDTO
from ._input import dtoFromInput


class ClassificationService:
    """Classe qui représente le service de gestion des classifications."""

    def __init__(self, classificationDAO: ClassificationDAO) -> None:
        self._classificationDAO = classificationDAO

    def getAllClassifications(self) -> List[ClassificationDTO]:
        """
        Méthode qui récupère toutes les classifications.

        :return: Liste des DTO de classifications.
        """
        return self._classificationDAO.getAll()

    def getClassificationsByMinAge(self, minAge: int) -> List[ClassificationDTO]:
        """
        Méthode qui récupère les classifications d'un âge minimum donné.

        :param minAge: Âge minimum recherché.
        :return: Liste des classifications correspondantes.
        """
        return self._classificationDAO.getByMinAge(minAge)

    def getClassificationById(self, idClassification: int) -> ClassificationDTO:
        """
        Méthode qui récupère une classification par son identifiant.

        :param idClassification: Identifiant de la classification.
        :return: DTO de la classification.
        :raises NotFoundError: Si la classification n'existe pas.
        """
        classification = self._classificationDAO.getById(idClassification)
        if classification is None:
            raise NotFoundError(f"Classification {idClassification} not found")
        return classification

    def createClassification(self, data: Any) -> ClassificationDTO:
        """
        Méthode qui crée une classification.

        :param data: Données de la classification.
        :return: DTO de la classification créée.
        :raises InvalidRequestError: Si les données sont invalides.
        :raises AlreadyExistsError: Si l'identifiant existe déjà.
        """
        classification = dtoFromInput(data, ClassificationDTO.fromDictWithoutId)
        try:
            return self._classificationDAO.create(classification)
        except DuplicateKeyError:
            raise AlreadyExistsError(
                f"Classification {classification.idClassification} already exists"
            )

    def updateClassification(
        self, idClassification: int, data: Any
    ) -> ClassificationDTO:
        """
        Méthode qui remplace les données d'une classification.

        :param idClassification: Identifiant de la classification à modifier.
        :param data: Nouvelles données de la classification.
        :return: DTO de la classification modifiée.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises NotFoundError: Si la classification n'existe pas.
        """
        if (
            isinstance(data, dict)
            and "idClassification" in data
            and data["idClassification"] != idClassification
        ):
            raise InvalidRequestError(
                "idClassification in the URL and in the body must match"
            )
        classification = dtoFromInput(data, ClassificationDTO.fromDictWithoutId)
        classification.idClassification = idClassification
        if not self._classificationDAO.update(classification):
            raise NotFoundError(
                f"Classification {classification.idClassification} not found"
            )
        return classification

    def deleteClassification(self, idClassification: int) -> None:
        """
        Méthode qui supprime une classification.

        :param idClassification: Identifiant de la classification à supprimer.
        :raises NotFoundError: Si la classification n'existe pas.
        """
        if not self._classificationDAO.delete(idClassification):
            raise NotFoundError(f"Classification {idClassification} not found")