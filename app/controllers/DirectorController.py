from flask import Blueprint, jsonify, request

from ..services import DirectorService
from ..decorators import requireRole
from ..models import UserRole

def createDirectorBlueprint(directorService: DirectorService) -> Blueprint:
    blueprint = Blueprint("directors", __name__, url_prefix="/directors")

    @blueprint.get("")
    def getDirectors():
        """
        Récupérer les réalisateurs, avec une recherche facultative par nom.
        ---
        tags:
          - Directors
        security: []
        parameters:
          - name: name
            in: query
            type: string
            required: false
            description: Recherche partielle sur le nom ou le prénom.
            example: Nolan
        responses:
          200:
            description: Liste des réalisateurs.
            schema:
              type: array
              items:
                $ref: '#/definitions/Director'
        """
        name = request.args.get("name")
        directors = (
            directorService.searchDirectorsByName(name)
            if name
            else directorService.getAllDirectors()
        )
        return jsonify([director.toDict() for director in directors]), 200

    @blueprint.get("/<int:idDirector>")
    def getDirector(idDirector: int):
        """
        Récupérer un réalisateur par son identifiant.
        ---
        tags:
          - Directors
        security: []
        parameters:
          - name: idDirector
            in: path
            type: integer
            required: true
            description: Identifiant du réalisateur.
        responses:
          200:
            description: Réalisateur trouvé.
            schema:
              $ref: '#/definitions/Director'
          404:
            description: Réalisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        director = directorService.getDirectorById(idDirector)
        return jsonify(director.toDict()), 200

    @blueprint.post("")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def createDirector():
        """
        Créer un réalisateur.
        ---
        tags:
          - Directors
        consumes:
          - application/json
        parameters:
          - in: body
            name: director
            required: true
            schema:
              $ref: '#/definitions/DirectorInput'
        responses:
          201:
            description: Réalisateur créé.
            schema:
              $ref: '#/definitions/Director'
          400:
            description: Corps JSON absent, invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Conflit d'identifiant.
            schema:
              $ref: '#/definitions/Error'
        """
        director = directorService.createDirector(request.get_json(silent=True))
        return jsonify(director.toDict()), 201

    @blueprint.put("/<int:idDirector>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def updateDirector(idDirector: int):
        """
        Remplacer un réalisateur existant.
        ---
        tags:
          - Directors
        consumes:
          - application/json
        parameters:
          - name: idDirector
            in: path
            type: integer
            required: true
            description: Identifiant du réalisateur à modifier.
          - in: body
            name: director
            required: true
            schema:
              $ref: '#/definitions/DirectorInput'
        responses:
          200:
            description: Réalisateur modifié.
            schema:
              $ref: '#/definitions/Director'
          400:
            description: Corps invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Réalisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        updatedDirector = directorService.updateDirector(
            idDirector, request.get_json(silent=True)
        )
        return jsonify(updatedDirector.toDict()), 200

    @blueprint.delete("/<int:idDirector>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def deleteDirector(idDirector: int):
        """
        Supprimer un réalisateur.
        ---
        tags:
          - Directors
        parameters:
          - name: idDirector
            in: path
            type: integer
            required: true
            description: Identifiant du réalisateur à supprimer.
        responses:
          204:
            description: Réalisateur supprimé.
          404:
            description: Réalisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        directorService.deleteDirector(idDirector)
        return "", 204

    return blueprint
