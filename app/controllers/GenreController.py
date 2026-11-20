from typing import Any

from flask import Blueprint, jsonify, request

from ..Exceptions import InvalidRequestError
from ..models import GenreDTO
from ..services import GenreService


def _toGenreDTO(data: Any) -> GenreDTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return GenreDTO.fromDictWithoutId(data)
    except (KeyError, TypeError) as e:
        raise InvalidRequestError(f"Invalid or missing field: {e}")


def createGenreBlueprint(genreService: GenreService) -> Blueprint:
    blueprint = Blueprint("genres", __name__, url_prefix="/genres")

    @blueprint.get("")
    def getGenres():
        """
        Récupérer tous les genres ou rechercher par nom.
        ---
        tags:
          - Genres
        parameters:
          - name: name
            in: query
            type: string
            required: false
            description: Nom ou partie du nom du genre recherché.
            example: Science-fiction
        responses:
          200:
            description: Liste des genres.
            schema:
              type: array
              items:
                $ref: '#/definitions/Genre'
        """
        name = request.args.get("name")
        genres = (
            genreService.searchGenresByName(name) if name else genreService.getAllGenres()
        )
        return jsonify([genre.toDict() for genre in genres]), 200

    @blueprint.get("/<int:idGenre>")
    def getGenre(idGenre: int):
        """
        Récupérer un genre par son identifiant.
        ---
        tags:
          - Genres
        parameters:
          - name: idGenre
            in: path
            type: integer
            required: true
            description: Identifiant du genre.
        responses:
          200:
            description: Genre trouvé.
            schema:
              $ref: '#/definitions/Genre'
          404:
            description: Genre introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        genre = genreService.getGenreById(idGenre)
        return jsonify(genre.toDict()), 200

    @blueprint.post("")
    def createGenre():
        """
        Créer un genre.
        ---
        tags:
          - Genres
        consumes:
          - application/json
        parameters:
          - in: body
            name: genre
            required: true
            schema:
              $ref: '#/definitions/GenreInput'
        responses:
          201:
            description: Genre créé.
            schema:
              $ref: '#/definitions/Genre'
          400:
            description: Corps JSON absent, invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Un genre avec cet identifiant existe déjà.
            schema:
              $ref: '#/definitions/Error'
        """
        genre = genreService.createGenre(_toGenreDTO(request.get_json(silent=True)))
        return jsonify(genre.toDict()), 201

    return blueprint