from typing import Any

from flask import Blueprint, jsonify, request

from ..Exceptions import InvalidRequestError
from ..models import DirectorDTO
from ..services import DirectorService


def _toDirectorDTO(data: Any) -> DirectorDTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return DirectorDTO.fromDictWithoutId(data)
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidRequestError(f"Invalid or missing field: {error}")


def createDirectorBlueprint(directorService: DirectorService) -> Blueprint:
    blueprint = Blueprint("directors", __name__, url_prefix="/directors")

    @blueprint.get("")
    def getDirectors():
        """
        Récupérer les réalisateurs, avec une recherche facultative par nom.
        ---
        tags:
          - Directors
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
        director = directorService.createDirector(
            _toDirectorDTO(request.get_json(silent=True))
        )
        return jsonify(director.toDict()), 201

    @blueprint.put("/<int:idDirector>")
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
        data = request.get_json(silent=True)
        if isinstance(data, dict) and "idDirector" in data and data["idDirector"] != idDirector:
            raise InvalidRequestError("idDirector in the URL and in the body must match")
        director = _toDirectorDTO(data)
        director.idDirector = idDirector
        updatedDirector = directorService.updateDirector(director)
        return jsonify(updatedDirector.toDict()), 200

    @blueprint.delete("/<int:idDirector>")
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
