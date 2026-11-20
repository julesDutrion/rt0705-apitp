from flask import Blueprint, jsonify, request

from ..models import DirectorDTO
from ..services import DirectorService


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
            description: Texte utilisé pour rechercher un réalisateur par son nom.
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
            description: Un réalisateur avec cet identifiant existe déjà.
            schema:
              $ref: '#/definitions/Error'
        """
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Invalid JSON body"}), 400
        try:
            director = DirectorDTO.fromDictWithoutId(data)
        except (KeyError, TypeError) as e:
            return jsonify({"error": f"Invalid or missing field: {e}"}), 400
        directorService.createDirector(director)
        return jsonify(director.toDict()), 201

    return blueprint