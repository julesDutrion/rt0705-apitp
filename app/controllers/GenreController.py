from typing import Any

from flask import Blueprint, jsonify, request

from Exceptions import InvalidRequestError
from models import GenreDTO
from services import GenreService


def _toGenreDTO(data: Any) -> GenreDTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return GenreDTO.fromDict(data)
    except (KeyError, TypeError) as e:
        raise InvalidRequestError(f"Invalid or missing field: {e}")


def createGenreBlueprint(genreService: GenreService) -> Blueprint:
    blueprint = Blueprint("genres", __name__, url_prefix="/genres")

    @blueprint.get("")
    def getGenres():
        name = request.args.get("name")
        genres = (
            genreService.searchGenresByName(name) if name else genreService.getAllGenres()
        )
        return jsonify([genre.toDict() for genre in genres]), 200

    @blueprint.get("/<int:idGenre>")
    def getGenre(idGenre: int):
        genre = genreService.getGenreById(idGenre)
        return jsonify(genre.toDict()), 200

    @blueprint.post("")
    def createGenre():
        genre = genreService.createGenre(_toGenreDTO(request.get_json(silent=True)))
        return jsonify(genre.toDict()), 201

    return blueprint