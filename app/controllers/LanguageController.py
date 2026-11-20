from typing import Any
 
from flask import Blueprint, jsonify, request
 
from ..Exceptions import InvalidRequestError
from ..models.LanguageDTO import LanguageDTO
from ..services.LanguageService import LanguageService
 
 
def _toLanguageDTO(data: Any) -> LanguageDTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return LanguageDTO.fromDict(data)
    except (KeyError, TypeError) as e:
        raise InvalidRequestError(f"Invalid or missing field: {e}")
 
 
def createLanguageBlueprint(languageService: LanguageService) -> Blueprint:
    blueprint = Blueprint("languages", __name__, url_prefix="/languages")
 
    @blueprint.get("")
    def getLanguages():
        """
        Récupérer toutes les langues disponibles.
        ---
        tags:
          - Languages
        responses:
          200:
            description: Liste des langues.
            schema:
              type: array
              items:
                $ref: '#/definitions/Language'
        """
        languages = languageService.getAllLanguages()
        return jsonify([language.toDict() for language in languages]), 200
 
    @blueprint.get("/<int:idLanguage>")
    def getLanguage(idLanguage: int):
        """
        Récupérer une langue par son identifiant.
        ---
        tags:
          - Languages
        parameters:
          - name: idLanguage
            in: path
            type: integer
            required: true
            description: Identifiant de la langue.
        responses:
          200:
            description: Langue trouvée.
            schema:
              $ref: '#/definitions/Language'
          404:
            description: Langue introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        language = languageService.getLanguageById(idLanguage)
        return jsonify(language.toDict()), 200
 
    @blueprint.get("/code/<string:code>")
    def getLanguageByCode(code: str):
        """
        Récupérer une langue par son code.
        ---
        tags:
          - Languages
        parameters:
          - name: code
            in: path
            type: string
            required: true
            description: Code de la langue.
            example: fr
        responses:
          200:
            description: Langue trouvée.
            schema:
              $ref: '#/definitions/Language'
          404:
            description: Langue introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        language = languageService.getLanguageByCode(code)
        return jsonify(language.toDict()), 200
 
    @blueprint.post("")
    def createLanguage():
        """
        Créer une langue.
        ---
        tags:
          - Languages
        consumes:
          - application/json
        parameters:
          - in: body
            name: language
            required: true
            schema:
              $ref: '#/definitions/Language'
        responses:
          201:
            description: Langue créée.
            schema:
              $ref: '#/definitions/Language'
          400:
            description: Corps JSON absent, invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Une langue avec cet identifiant existe déjà.
            schema:
              $ref: '#/definitions/Error'
        """
        language = languageService.createLanguage(
            _toLanguageDTO(request.get_json(silent=True))
        )
        return jsonify(language.toDict()), 201
 
    return blueprint
