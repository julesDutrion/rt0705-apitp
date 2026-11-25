from typing import Any, List

from pymongo.errors import DuplicateKeyError

from ..dao import GenreDAO
from ..Exceptions import AlreadyExistsError, InvalidRequestError, NotFoundError
from ..models import GenreDTO
from ._input import dtoFromInput


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

    def createGenre(self, data: Any) -> GenreDTO:
        genre = dtoFromInput(data, GenreDTO.fromDictWithoutId)
        try:
            return self._genreDAO.create(genre)
        except DuplicateKeyError:
            raise AlreadyExistsError(f"Genre {genre.idGenre} already exists")

    def updateGenre(self, idGenre: int, data: Any) -> GenreDTO:
        if (
            isinstance(data, dict)
            and "idGenre" in data
            and data["idGenre"] != idGenre
        ):
            raise InvalidRequestError(
                "idGenre in the URL and in the body must match"
            )
        genre = dtoFromInput(data, GenreDTO.fromDictWithoutId)
        genre.idGenre = idGenre
        if not self._genreDAO.update(genre):
            raise NotFoundError(f"Genre {genre.idGenre} not found")
        return genre

    def deleteGenre(self, idGenre: int) -> None:
        if not self._genreDAO.delete(idGenre):
            raise NotFoundError(f"Genre {idGenre} not found")