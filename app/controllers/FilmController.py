from typing import Any, List

from flask import Blueprint, jsonify, request
from werkzeug.datastructures import MultiDict

from ..Exceptions import InvalidRequestError
from ..models.FilmDTO import FilmDTO
from ..services.FilmService import FilmService


def _toFilmDTO(data: Any) -> FilmDTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return FilmDTO.fromDict(data)
    except (KeyError, TypeError, ValueError) as e:
        raise InvalidRequestError(f"Invalid or missing field: {e}")


def _findFilms(filmService: FilmService, args: MultiDict) -> List[FilmDTO]:
    filters = {
        "title": args.get("title"),
        "genre": args.get("genre", type=int),
        "director": args.get("director", type=int),
        "actor": args.get("actor", type=int),
        "language": args.get("language", type=int)
    }

    return filmService.searchFilms(filters)


def createFilmBlueprint(filmService: FilmService) -> Blueprint:
    blueprint = Blueprint("films", __name__, url_prefix="/films")

    @blueprint.get("")
    def getFilms():
        films = _findFilms(filmService, request.args)
        return jsonify([film.toDict() for film in films]), 200

    @blueprint.get("/<string:idFilm>")
    def getFilm(idFilm: str):
        film = filmService.getFilmById(idFilm)
        return jsonify(film.toDict()), 200

    @blueprint.post("")
    def createFilm():
        film = filmService.createFilm(_toFilmDTO(request.get_json(silent=True)))
        return jsonify(film.toDict()), 201

    @blueprint.put("/<string:idFilm>")
    def updateFilm(idFilm: str):
        film = _toFilmDTO(request.get_json(silent=True))
        if film.idFilm != idFilm:
            raise InvalidRequestError("idFilm in the URL and in the body must match")
        updatedFilm = filmService.updateFilm(film)
        return jsonify(updatedFilm.toDict()), 200

    @blueprint.delete("/<string:idFilm>")
    def deleteFilm(idFilm: str):
        filmService.deleteFilm(idFilm)
        return "", 204

    return blueprint