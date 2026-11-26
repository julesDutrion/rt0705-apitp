from flask import Blueprint, jsonify, request

from ..services import GenreService
from ..decorators import requireRole
from ..models import UserRole

def createGenreBlueprint(genreService: GenreService) -> Blueprint:
    blueprint = Blueprint("genres", __name__, url_prefix="/genres")

    @blueprint.get("")
    def getGenres():
        """
        Récupérer tous les genres ou rechercher par nom.
        ---
        tags:
          - Genres
        security: []
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
        security: []
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
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
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
        genre = genreService.createGenre(request.get_json(silent=True))
        return jsonify(genre.toDict()), 201

    @blueprint.put("/<int:idGenre>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
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
        updatedGenre = genreService.updateGenre(
            idGenre, request.get_json(silent=True)
        )
        return jsonify(updatedGenre.toDict()), 200

    @blueprint.delete("/<int:idGenre>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
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
