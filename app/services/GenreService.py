from typing import List

from pymongo.errors import DuplicateKeyError

from dao import GenreDAO
from ..Exceptions import AlreadyExistsError, NotFoundError
from ..models.GenreDTO import GenreDTO


class GenreService:
    def __init__(self, genreDAO: GenreDAO) -> None:
        self._genreDAO = genreDAO

    def getAllGenres(self) -> List[GenreDTO]:
        return self._genreDAO.getAll()

    def searchGenresByName(self, name: str) -> List[GenreDTO]:
        return self._genreDAO.searchByName(name)

    def getGenreById(self, idGenre: int) -> GenreDTO:
        genre = self._genreDAO.getById(idGenre)
        if genre is None:
            raise NotFoundError(f"Genre {idGenre} not found")
        return genre

    def createGenre(self, genre: GenreDTO) -> GenreDTO:
        try:
            return self._genreDAO.create(genre)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Genre {genre.idGenre} already exists")