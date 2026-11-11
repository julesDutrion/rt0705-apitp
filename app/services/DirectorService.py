from typing import List

from pymongo.errors import DuplicateKeyError

from dao import DirectorDAO
from ..Exceptions import AlreadyExistsError, NotFoundError
from ..models.DirectorDTO import DirectorDTO


class DirectorService:
    def __init__(self, directorDAO: DirectorDAO) -> None:
        self._directorDAO = directorDAO

    def getAllDirectors(self) -> List[DirectorDTO]:
        return self._directorDAO.getAll()

    def searchDirectorsByName(self, name: str) -> List[DirectorDTO]:
        return self._directorDAO.searchByName(name)

    def getDirectorById(self, idDirector: int) -> DirectorDTO:
        director = self._directorDAO.getById(idDirector)
        if director is None:
            raise NotFoundError(f"Director {idDirector} not found")
        return director

    def createDirector(self, director: DirectorDTO) -> DirectorDTO:
        try:
            return self._directorDAO.create(director)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Director {director.idDirector} already exists")