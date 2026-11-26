from flask import Blueprint, jsonify, request

from ..services import ClassificationService
from ..decorators import requireRole
from ..models import UserRole

def createClassificationBlueprint(
    classificationService: ClassificationService,
) -> Blueprint:
    blueprint = Blueprint("classifications", __name__, url_prefix="/classifications")

    @blueprint.get("")
    def getClassifications():
        """
        Récupérer toutes les classifications ou filtrer par âge minimum.
        ---
        tags:
          - Classifications
        security: []
        parameters:
          - name: minAge
            in: query
            type: integer
            required: false
            description: Filtre les classifications selon leur âge minimum.
            example: 12
        responses:
          200:
            description: Liste des classifications.
            schema:
              type: array
              items:
                $ref: '#/definitions/Classification'
        """
        minAge = request.args.get("minAge", type=int)
        classifications = (
            classificationService.getClassificationsByMinAge(minAge)
            if minAge is not None
            else classificationService.getAllClassifications()
        )
        return jsonify([c.toDict() for c in classifications]), 200

    @blueprint.get("/<int:idClassification>")
    def getClassification(idClassification: int):
        """
        Récupérer une classification par son identifiant.
        ---
        tags:
          - Classifications
        security: []
        parameters:
          - name: idClassification
            in: path
            type: integer
            required: true
            description: Identifiant de la classification.
        responses:
          200:
            description: Classification trouvée.
            schema:
              $ref: '#/definitions/Classification'
          404:
            description: Classification introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        classification = classificationService.getClassificationById(idClassification)
        return jsonify(classification.toDict()), 200

    @blueprint.post("")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def createClassification():
        """
        Créer une classification.
        ---
        tags:
          - Classifications
        consumes:
          - application/json
        parameters:
          - in: body
            name: classification
            required: true
            schema:
              $ref: '#/definitions/ClassificationInput'
        responses:
          201:
            description: Classification créée.
            schema:
              $ref: '#/definitions/Classification'
          400:
            description: Corps JSON absent, invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Une classification avec cet identifiant existe déjà.
            schema:
              $ref: '#/definitions/Error'
        """
        classification = classificationService.createClassification(
            request.get_json(silent=True)
        )
        return jsonify(classification.toDict()), 201

    @blueprint.put("/<int:idClassification>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def updateClassification(idClassification: int):
        """
        Remplacer une classification existante.
        ---
        tags:
          - Classifications
        consumes:
          - application/json
        parameters:
          - name: idClassification
            in: path
            type: integer
            required: true
            description: Identifiant de la classification à modifier.
          - in: body
            name: classification
            required: true
            schema:
              $ref: '#/definitions/ClassificationInput'
        responses:
          200:
            description: Classification modifiée.
            schema:
              $ref: '#/definitions/Classification'
          400:
            description: Corps invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Classification introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        updatedClassification = classificationService.updateClassification(
            idClassification, request.get_json(silent=True)
        )
        return jsonify(updatedClassification.toDict()), 200

    @blueprint.delete("/<int:idClassification>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def deleteClassification(idClassification: int):
        """
        Supprimer une classification.
        ---
        tags:
          - Classifications
        parameters:
          - name: idClassification
            in: path
            type: integer
            required: true
            description: Identifiant de la classification à supprimer.
        responses:
          204:
            description: Classification supprimée.
          404:
            description: Classification introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        classificationService.deleteClassification(idClassification)
        return "", 204

    return blueprint