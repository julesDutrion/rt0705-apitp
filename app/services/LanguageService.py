from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import LanguageDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import LanguageDTO
from ._input import dtoFromInput


class LanguageService:
    """Classe qui représente le service de gestion des langues."""

    def __init__(self, languageDAO: LanguageDAO) -> None:
        self._languageDAO = languageDAO

    def getAllLanguages(self) -> List[LanguageDTO]:
        """
        Méthode qui récupère toutes les langues.

        :return: Liste des DTO de langues.
        """
        return self._languageDAO.getAll()

    def searchLanguagesByName(self, name: str) -> List[LanguageDTO]:
        """
        Méthode qui recherche les langues par nom.

        :param name: Texte recherché.
        :return: Liste des langues correspondantes.
        """
        return self._languageDAO.searchByName(name)

    def getLanguageById(self, idLanguage: int) -> LanguageDTO:
        """
        Méthode qui récupère une langue par son identifiant.

        :param idLanguage: Identifiant de la langue.
        :return: DTO de la langue.
        :raises NotFoundError: Si la langue n'existe pas.
        """
        language = self._languageDAO.getById(idLanguage)
        if language is None:
            raise NotFoundError(f"Language {idLanguage} not found")
        return language

    def getLanguageByCode(self, code: str) -> LanguageDTO:
        """
        Méthode qui récupère une langue par son code.

        :param code: Code de la langue.
        :return: DTO de la langue.
        :raises NotFoundError: Si aucune langue ne correspond au code.
        """
        language = self._languageDAO.getByCode(code)
        if language is None:
            raise NotFoundError(f"Language with code '{code}' not found")
        return language

    def createLanguage(self, data: Any) -> LanguageDTO:
        """
        Méthode qui crée une langue.

        :param data: Données de la langue.
        :return: DTO de la langue créée.
        :raises InvalidRequestError: Si les données sont invalides.
        :raises AlreadyExistsError: Si l'identifiant existe déjà.
        """
        language = dtoFromInput(data, LanguageDTO.fromDictWithoutId)
        language.code = language.code.lower()
        try:
            return self._languageDAO.create(language)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Language {language.idLanguage} already exists")

    def updateLanguage(self, idLanguage: int, data: Any) -> LanguageDTO:
        """
        Méthode qui remplace les données d'une langue.

        :param idLanguage: Identifiant de la langue à modifier.
        :param data: Nouvelles données de la langue.
        :return: DTO de la langue modifiée.
        :raises InvalidRequestError: Si les données ou l'identifiant sont invalides.
        :raises NotFoundError: Si la langue n'existe pas.
        """
        if (
            isinstance(data, dict)
            and "idLanguage" in data
            and data["idLanguage"] != idLanguage
        ):
            raise InvalidRequestError(
                "idLanguage in the URL and in the body must match"
            )
        language = dtoFromInput(data, LanguageDTO.fromDictWithoutId)
        language.idLanguage = idLanguage
        if not self._languageDAO.update(language):
            raise NotFoundError(f"Language {language.idLanguage} not found")
        return language

    def deleteLanguage(self, idLanguage: int) -> None:
        """
        Méthode qui supprime une langue.

        :param idLanguage: Identifiant de la langue à supprimer.
        :raises NotFoundError: Si la langue n'existe pas.
        """
        if not self._languageDAO.delete(idLanguage):
            raise NotFoundError(f"Language {idLanguage} not found")