from typing import Any, List

from flask import Blueprint, jsonify, request
from werkzeug.datastructures import MultiDict

from ..Exceptions import InvalidRequestError
from ..models import FilmDTO
from ..services import FilmService


def _toFilmDTO(data: Any) -> FilmDTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return FilmDTO.fromDictWithoutId(data)
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
        """
        Rechercher les films selon un ou plusieurs critères.
        ---
        tags:
          - Films
        parameters:
          - name: title
            in: query
            type: string
            required: false
            description: Titre ou partie du titre recherché.
          - name: genre
            in: query
            type: integer
            required: false
            description: Identifiant du genre.
          - name: director
            in: query
            type: integer
            required: false
            description: Identifiant du réalisateur.
          - name: actor
            in: query
            type: integer
            required: false
            description: Identifiant de l'acteur.
          - name: language
            in: query
            type: integer
            required: false
            description: Identifiant de la langue.
        responses:
          200:
            description: Liste des films correspondant aux critères.
            schema:
              type: array
              items:
                $ref: '#/definitions/Film'
        """
        films = _findFilms(filmService, request.args)
        return jsonify([film.toDict() for film in films]), 200

    @blueprint.get("/<string:idFilm>")
    def getFilm(idFilm: str):
        """
        Récupérer un film par son identifiant.
        ---
        tags:
          - Films
        parameters:
          - name: idFilm
            in: path
            type: string
            required: true
            description: Identifiant du film.
        responses:
          200:
            description: Film trouvé.
            schema:
              $ref: '#/definitions/Film'
          404:
            description: Film introuvable ou non accessible.
            schema:
              $ref: '#/definitions/Error'
        """
        film = filmService.getFilmById(idFilm)
        return jsonify(film.toDict()), 200

    @blueprint.post("")
    def createFilm():
        """
        Ajouter un film.
        ---
        tags:
          - Films
        consumes:
          - application/json
        parameters:
          - in: body
            name: film
            required: true
            schema:
              $ref: '#/definitions/FilmInput'
        responses:
          201:
            description: Film créé.
            schema:
              $ref: '#/definitions/Film'
          400:
            description: Corps JSON absent, invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Un film avec cet identifiant existe déjà.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Une référence (réalisateur, classification, langue ou genre) est invalide.
            schema:
              $ref: '#/definitions/Error'
        """
        film = filmService.createFilm(_toFilmDTO(request.get_json(silent=True)))
        return jsonify(film.toDict()), 201

    @blueprint.put("/<string:idFilm>")
    def updateFilm(idFilm: str):
        """
        Modifier un film existant.
        ---
        tags:
          - Films
        consumes:
          - application/json
        parameters:
          - name: idFilm
            in: path
            type: string
            required: true
            description: Identifiant du film à modifier.
          - in: body
            name: film
            required: true
            schema:
              $ref: '#/definitions/FilmInput'
        responses:
          200:
            description: Film modifié.
            schema:
              $ref: '#/definitions/Film'
          400:
            description: Corps JSON invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Film à modifier introuvable.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Une référence (réalisateur, classification, langue ou genre) est invalide.
            schema:
              $ref: '#/definitions/Error'
        """
        data = request.get_json(silent=True)
        if isinstance(data, dict) and "idFilm" in data and data["idFilm"] != idFilm:
            raise InvalidRequestError("idFilm in the URL and in the body must match")
        film = _toFilmDTO(data)
        film.idFilm = idFilm
        updatedFilm = filmService.updateFilm(film)
        return jsonify(updatedFilm.toDict()), 200

    @blueprint.delete("/<string:idFilm>")
    def deleteFilm(idFilm: str):
        """
        Supprimer un film.
        ---
        tags:
          - Films
        parameters:
          - name: idFilm
            in: path
            type: string
            required: true
            description: Identifiant du film à supprimer.
        responses:
          204:
            description: Film supprimé. Aucun contenu n'est renvoyé.
          404:
            description: Film introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        filmService.deleteFilm(idFilm)
        return "", 204

    return blueprint