from flask import Blueprint, jsonify, request

from ..services import UserService


def createUserBlueprint(userService: UserService) -> Blueprint:
    blueprint = Blueprint("users", __name__, url_prefix="/users")

    @blueprint.post("")
    def createUser():
        """
        Créer un utilisateur.
        ---
        tags:
          - Users
        consumes:
          - application/json
        parameters:
          - in: body
            name: user
            required: true
            schema:
              $ref: '#/definitions/UserInput'
        responses:
          201:
            description: Utilisateur créé. Le hash du mot de passe n'est jamais exposé.
            schema:
              $ref: '#/definitions/User'
          400:
            description: Corps invalide ou informations utilisateur invalides.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Le login ou l'adresse e-mail est déjà utilisé.
            schema:
              $ref: '#/definitions/Error'
        """
        user = userService.createUser(request.get_json(silent=True))
        return jsonify(user.toPublicDict()), 201

    @blueprint.get("/<int:idUser>")
    def getUser(idUser: int):
        """
        Récupérer un utilisateur par son identifiant.
        ---
        tags:
          - Users
        parameters:
          - name: idUser
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Utilisateur trouvé.
            schema:
              $ref: '#/definitions/User'
          404:
            description: Utilisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        user = userService.getUserById(idUser)
        return jsonify(user.toPublicDict()), 200

    @blueprint.get("/login/<string:login>")
    def getUserByLogin(login: str):
        """
        Récupérer un utilisateur par son login.
        ---
        tags:
          - Users
        parameters:
          - name: login
            in: path
            type: string
            required: true
        responses:
          200:
            description: Utilisateur trouvé.
            schema:
              $ref: '#/definitions/User'
          404:
            description: Utilisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        user = userService.getUserByLogin(login)
        return jsonify(user.toPublicDict()), 200

    @blueprint.put("/<int:idUser>")
    def updateUser(idUser: int):
        """
        Modifier un utilisateur.
        ---
        tags:
          - Users
        consumes:
          - application/json
        parameters:
          - name: idUser
            in: path
            type: integer
            required: true
          - in: body
            name: user
            required: true
            schema:
              $ref: '#/definitions/UserUpdateInput'
        responses:
          200:
            description: Utilisateur modifié.
            schema:
              $ref: '#/definitions/User'
          400:
            description: Corps invalide ou informations utilisateur invalides.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Utilisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Le login ou l'adresse e-mail est déjà utilisé.
            schema:
              $ref: '#/definitions/Error'
        """
        user = userService.updateUser(
            idUser, request.get_json(silent=True)
        )
        return jsonify(user.toPublicDict()), 200

    @blueprint.delete("/<int:idUser>")
    def deleteUser(idUser: int):
        """
        Supprimer un utilisateur.
        ---
        tags:
          - Users
        parameters:
          - name: idUser
            in: path
            type: integer
            required: true
        responses:
          204:
            description: Utilisateur supprimé.
          404:
            description: Utilisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        userService.deleteUser(idUser)
        return "", 204

    return blueprint
