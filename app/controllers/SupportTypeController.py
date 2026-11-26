from flask import Blueprint, jsonify, request

from ..services import SupportTypeService
from ..decorators import requireRole
from ..models import UserRole

def createSupportTypeBlueprint(
    supportTypeService: SupportTypeService,
) -> Blueprint:
    blueprint = Blueprint(
        "support_types", __name__, url_prefix="/support-types"
    )

    @blueprint.get("")
    def getSupportTypes():
        """
        Lister les types de supports.
        ---
        tags:
          - Types de supports
        security: []
        responses:
          200:
            description: Liste des types de supports.
            schema:
              type: array
              items:
                $ref: '#/definitions/SupportType'
        """
        types = supportTypeService.getAllSupportTypes()
        return jsonify([supportType.toDict() for supportType in types]), 200

    @blueprint.get("/<int:idSupportType>")
    def getSupportType(idSupportType: int):
        """
        Récupérer un type de support.
        ---
        tags:
          - Types de supports
        security: []
        parameters:
          - name: idSupportType
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Type trouvé.
            schema:
              $ref: '#/definitions/SupportType'
          404:
            description: Type introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        supportType = supportTypeService.getSupportTypeById(idSupportType)
        return jsonify(supportType.toDict()), 200

    @blueprint.post("")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def createSupportType():
        """
        Créer un type de support.
        ---
        tags:
          - Types de supports
        consumes:
          - application/json
        parameters:
          - in: body
            name: supportType
            required: true
            schema:
              $ref: '#/definitions/SupportTypeInput'
        responses:
          201:
            description: Type créé.
            schema:
              $ref: '#/definitions/SupportType'
          400:
            description: Corps invalide ou mode différent de physical/digital.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Conflit d'identifiant généré.
            schema:
              $ref: '#/definitions/Error'
        """
        supportType = supportTypeService.createSupportType(
            request.get_json(silent=True)
        )
        return jsonify(supportType.toDict()), 201

    @blueprint.put("/<int:idSupportType>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def updateSupportType(idSupportType: int):
        """
        Modifier un type de support.
        ---
        tags:
          - Types de supports
        consumes:
          - application/json
        parameters:
          - name: idSupportType
            in: path
            type: integer
            required: true
          - in: body
            name: supportType
            required: true
            schema:
              $ref: '#/definitions/SupportTypeInput'
        responses:
          200:
            description: Type modifié.
            schema:
              $ref: '#/definitions/SupportType'
          400:
            description: Corps invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Type introuvable.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Le mode ne peut pas changer si le type est utilisé.
            schema:
              $ref: '#/definitions/Error'
        """
        updated = supportTypeService.updateSupportType(
            idSupportType, request.get_json(silent=True)
        )
        return jsonify(updated.toDict()), 200

    @blueprint.delete("/<int:idSupportType>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def deleteSupportType(idSupportType: int):
        """
        Supprimer un type de support non utilisé.
        ---
        tags:
          - Types de supports
        parameters:
          - name: idSupportType
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Type supprimé.
          404:
            description: Type introuvable.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Le type est référencé par un support.
            schema:
              $ref: '#/definitions/Error'
        """
        supportTypeService.deleteSupportType(idSupportType)
        return "", 204

    return blueprint
