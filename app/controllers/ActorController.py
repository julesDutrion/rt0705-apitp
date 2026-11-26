from flask import Blueprint, jsonify, request

from ..services import ActorService
from ..decorators import requireRole
from ..models import UserRole


def createActorBlueprint(actorService: ActorService) -> Blueprint:
    blueprint = Blueprint("actors", __name__, url_prefix="/actors")

    @blueprint.get("")
    def getActors():
        """
        Récupérer tous les acteurs ou rechercher par nom.
        ---
        tags:
          - Actors
        security: []
        parameters:
          - name: name
            in: query
            type: string
            required: false
            description: Recherche partielle sur le prénom ou le nom.
            example: DiCaprio
        responses:
          200:
            description: Liste des acteurs.
            schema:
              type: array
              items:
                $ref: '#/definitions/Actor'
        """
        name = request.args.get("name")
        actors = (
            actorService.searchActorsByName(name)
            if name
            else actorService.getAllActors()
        )
        return jsonify([actor.toDict() for actor in actors]), 200

    @blueprint.get("/<int:idActor>")
    def getActor(idActor: int):
        """
        Récupérer un acteur par son identifiant.
        ---
        tags:
          - Actors
        security: []
        parameters:
          - name: idActor
            in: path
            type: integer
            required: true
            description: Identifiant de l'acteur.
        responses:
          200:
            description: Acteur trouvé.
            schema:
              $ref: '#/definitions/Actor'
          404:
            description: Acteur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        actor = actorService.getActorById(idActor)
        return jsonify(actor.toDict()), 200

    @blueprint.post("")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def createActor():
        """
        Créer un acteur.
        ---
        tags:
          - Actors
        consumes:
          - application/json
        parameters:
          - in: body
            name: actor
            required: true
            schema:
              $ref: '#/definitions/ActorInput'
        responses:
          201:
            description: Acteur créé.
            schema:
              $ref: '#/definitions/Actor'
          400:
            description: Corps JSON absent, invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Conflit d'identifiant.
            schema:
              $ref: '#/definitions/Error'
        """
        actor = actorService.createActor(request.get_json(silent=True))
        return jsonify(actor.toDict()), 201

    @blueprint.put("/<int:idActor>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def updateActor(idActor: int):
        """
        Remplacer un acteur existant.
        ---
        tags:
          - Actors
        consumes:
          - application/json
        parameters:
          - name: idActor
            in: path
            type: integer
            required: true
            description: Identifiant de l'acteur à modifier.
          - in: body
            name: actor
            required: true
            schema:
              $ref: '#/definitions/ActorInput'
        responses:
          200:
            description: Acteur modifié.
            schema:
              $ref: '#/definitions/Actor'
          400:
            description: Corps invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Acteur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        updatedActor = actorService.updateActor(
            idActor, request.get_json(silent=True)
        )
        return jsonify(updatedActor.toDict()), 200

    @blueprint.delete("/<int:idActor>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def deleteActor(idActor: int):
        """
        Supprimer un acteur.
        ---
        tags:
          - Actors
        parameters:
          - name: idActor
            in: path
            type: integer
            required: true
            description: Identifiant de l'acteur à supprimer.
        responses:
          204:
            description: Acteur supprimé.
          404:
            description: Acteur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        actorService.deleteActor(idActor)
        return "", 204

    return blueprint
