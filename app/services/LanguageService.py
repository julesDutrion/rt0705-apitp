from typing import List

from pymongo.errors import DuplicateKeyError

from dao import LanguageDAO
from ..Exceptions import AlreadyExistsError, NotFoundError
from ..models.LanguageDTO import LanguageDTO


class LanguageService:
    def __init__(self, languageDAO: LanguageDAO) -> None:
        self._languageDAO = languageDAO

    def getAllLanguages(self) -> List[LanguageDTO]:
        return self._languageDAO.getAll()

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

    def createLanguage(self, language: LanguageDTO) -> LanguageDTO:
        try:
            return self._languageDAO.create(language)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Language {language.idLanguage} already exists")