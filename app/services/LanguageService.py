from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import LanguageDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import LanguageDTO
from ._input import dtoFromInput


class LanguageService:
    def __init__(self, languageDAO: LanguageDAO) -> None:
        self._languageDAO = languageDAO

    def getAllLanguages(self) -> List[LanguageDTO]:
        return self._languageDAO.getAll()

    def searchLanguagesByName(self, name: str) -> List[LanguageDTO]:
        return self._languageDAO.searchByName(name)

    def getLanguageById(self, idLanguage: int) -> LanguageDTO:
        language = self._languageDAO.getById(idLanguage)
        if language is None:
            raise NotFoundError(f"Language {idLanguage} not found")
        return language

    def getLanguageByCode(self, code: str) -> LanguageDTO:
        language = self._languageDAO.getByCode(code)
        if language is None:
            raise NotFoundError(f"Language with code '{code}' not found")
        return language

    def createLanguage(self, data: Any) -> LanguageDTO:
        language = dtoFromInput(data, LanguageDTO.fromDictWithoutId)
        language.code = language.code.lower()
        try:
            return self._languageDAO.create(language)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Language {language.idLanguage} already exists")

    def updateLanguage(self, idLanguage: int, data: Any) -> LanguageDTO:
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
        if not self._languageDAO.delete(idLanguage):
            raise NotFoundError(f"Language {idLanguage} not found")