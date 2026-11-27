from flask import Blueprint, jsonify, request

from ..services import SupportService
from ..decorators import requireRole
from ..models import UserRole

def createSupportBlueprint(supportService: SupportService) -> Blueprint:
    blueprint = Blueprint("supports", __name__, url_prefix="/supports")

    @blueprint.get("")
    def getSupports():
        """
        Lister les supports.
        ---
        tags:
          - Supports
        security: []
        responses:
          200:
            description: Liste des supports.
            schema:
              type: array
              items:
                $ref: '#/definitions/Support'
        """
        supports = supportService.getAllSupports()
        return jsonify(supportService.toPublicDicts(supports)), 200

    @blueprint.get("/film/<string:idFilm>")
    def getSupportsByFilm(idFilm: str):
        """
        Lister les supports associés à un film.
        ---
        tags:
          - Supports
        security: []
        parameters:
          - name: idFilm
            in: path
            type: string
            required: true
        responses:
          200:
            description: Supports du film.
            schema:
              type: array
              items:
                $ref: '#/definitions/Support'
          404:
            description: Film introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        supports = supportService.getSupportsByFilmId(idFilm)
        return jsonify(supportService.toPublicDicts(supports)), 200

    @blueprint.get("/<int:idSupport>")
    def getSupport(idSupport: int):
        """
        Récupérer un support.
        ---
        tags:
          - Supports
        security: []
        parameters:
          - name: idSupport
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Support trouvé.
            schema:
              $ref: '#/definitions/Support'
          404:
            description: Support introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        support = supportService.getSupportById(idSupport)
        return jsonify(supportService.toPublicDict(support)), 200

    @blueprint.post("")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def createSupport():
        """
        Créer un support associé à un film et à un type.
        Pour physical, fournir location; pour digital, fournir une URL HTTP(S).
        ---
        tags:
          - Supports
        consumes:
          - application/json
        parameters:
          - in: body
            name: support
            required: true
            schema:
              $ref: '#/definitions/SupportInput'
        responses:
          201:
            description: Support créé.
            schema:
              $ref: '#/definitions/Support'
          400:
            description: Corps invalide ou données incompatibles avec le type.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Film ou type inexistant.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Conflit d'identifiant généré.
            schema:
              $ref: '#/definitions/Error'
        """
        support = supportService.createSupport(request.get_json(silent=True))
        return jsonify(supportService.toPublicDict(support)), 201

    @blueprint.put("/<int:idSupport>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def updateSupport(idSupport: int):
        """
        Modifier un support existant.
        ---
        tags:
          - Supports
        consumes:
          - application/json
        parameters:
          - name: idSupport
            in: path
            type: integer
            required: true
          - in: body
            name: support
            required: true
            schema:
              $ref: '#/definitions/SupportInput'
        responses:
          200:
            description: Support modifié.
            schema:
              $ref: '#/definitions/Support'
          400:
            description: Corps invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Support introuvable.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Film ou type inexistant.
            schema:
              $ref: '#/definitions/Error'
        """
        updated = supportService.updateSupport(
            idSupport, request.get_json(silent=True)
        )
        return jsonify(supportService.toPublicDict(updated)), 200

    @blueprint.delete("/<int:idSupport>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def deleteSupport(idSupport: int):
        """
        Supprimer un support.
        ---
        tags:
          - Supports
        parameters:
          - name: idSupport
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Support supprimé.
          404:
            description: Support introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        supportService.deleteSupport(idSupport)
        return "", 204

    return blueprint
