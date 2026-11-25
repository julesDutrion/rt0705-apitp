from flask import Blueprint, jsonify, request

from ..services import LanguageService


def createLanguageBlueprint(languageService: LanguageService) -> Blueprint:
    blueprint = Blueprint("languages", __name__, url_prefix="/languages")

    @blueprint.get("")
    def getLanguages():
        """
        Récupérer toutes les langues disponibles ou rechercher par nom.
        ---
        tags:
          - Languages
        parameters:
          - name: name
            in: query
            type: string
            required: false
            description: Nom ou partie du nom de la langue recherchée.
            example: French
        responses:
          200:
            description: Liste des langues.
            schema:
              type: array
              items:
                $ref: '#/definitions/Language'
        """
        name = request.args.get("name")
        languages = (
            languageService.searchLanguagesByName(name)
            if name
            else languageService.getAllLanguages()
        )
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
              $ref: '#/definitions/LanguageInput'
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
            description: Conflit d'identifiant.
            schema:
              $ref: '#/definitions/Error'
        """
        language = languageService.createLanguage(request.get_json(silent=True))
        return jsonify(language.toDict()), 201

    @blueprint.put("/<int:idLanguage>")
    def updateLanguage(idLanguage: int):
        """
        Remplacer une langue existante.
        ---
        tags:
          - Languages
        consumes:
          - application/json
        parameters:
          - name: idLanguage
            in: path
            type: integer
            required: true
            description: Identifiant de la langue à modifier.
          - in: body
            name: language
            required: true
            schema:
              $ref: '#/definitions/LanguageInput'
        responses:
          200:
            description: Langue modifiée.
            schema:
              $ref: '#/definitions/Language'
          400:
            description: Corps invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Langue introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        updatedLanguage = languageService.updateLanguage(
            idLanguage, request.get_json(silent=True)
        )
        return jsonify(updatedLanguage.toDict()), 200

    @blueprint.delete("/<int:idLanguage>")
    def deleteLanguage(idLanguage: int):
        """
        Supprimer une langue.
        ---
        tags:
          - Languages
        parameters:
          - name: idLanguage
            in: path
            type: integer
            required: true
            description: Identifiant de la langue à supprimer.
        responses:
          204:
            description: Langue supprimée.
          404:
            description: Langue introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        languageService.deleteLanguage(idLanguage)
        return "", 204

    return blueprint
