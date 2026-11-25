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
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidRequestError(f"Invalid or missing field: {error}")


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
            genreService.searchGenresByName(name)
            if name
            else genreService.getAllGenres()
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
            description: Conflit d'identifiant.
            schema:
              $ref: '#/definitions/Error'
        """
        genre = genreService.createGenre(_toGenreDTO(request.get_json(silent=True)))
        return jsonify(genre.toDict()), 201

    @blueprint.put("/<int:idGenre>")
    def updateGenre(idGenre: int):
        """
        Remplacer un genre existant.
        ---
        tags:
          - Genres
        consumes:
          - application/json
        parameters:
          - name: idGenre
            in: path
            type: integer
            required: true
            description: Identifiant du genre à modifier.
          - in: body
            name: genre
            required: true
            schema:
              $ref: '#/definitions/GenreInput'
        responses:
          200:
            description: Genre modifié.
            schema:
              $ref: '#/definitions/Genre'
          400:
            description: Corps invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Genre introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        data = request.get_json(silent=True)
        if isinstance(data, dict) and "idGenre" in data and data["idGenre"] != idGenre:
            raise InvalidRequestError("idGenre in the URL and in the body must match")
        genre = _toGenreDTO(data)
        genre.idGenre = idGenre
        updatedGenre = genreService.updateGenre(genre)
        return jsonify(updatedGenre.toDict()), 200

    @blueprint.delete("/<int:idGenre>")
    def deleteGenre(idGenre: int):
        """
        Supprimer un genre.
        ---
        tags:
          - Genres
        parameters:
          - name: idGenre
            in: path
            type: integer
            required: true
            description: Identifiant du genre à supprimer.
        responses:
          204:
            description: Genre supprimé.
          404:
            description: Genre introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        genreService.deleteGenre(idGenre)
        return "", 204

    return blueprint
