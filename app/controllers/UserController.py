from flask import Blueprint, g, jsonify, request

from ..decorators import requireRole
from ..Exceptions import InvalidRequestError
from ..models import UserRole
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
        security: []
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

    @blueprint.get("")
    @requireRole(UserRole.ADMIN)
    def getAllUsers():
        """
        Récupérer la liste de tous les utilisateurs.
        ---
        tags:
          - Users
        responses:
          200:
            description: Liste des utilisateurs sans leurs mots de passe.
            schema:
              type: array
              items:
                $ref: '#/definitions/User'
          401:
            description: Jeton d'authentification manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          403:
            description: Réservé aux administrateurs.
            schema:
              $ref: '#/definitions/Error'
        """
        users = userService.getAllUsers()
        return jsonify([user.toPublicDict() for user in users]), 200

    @blueprint.get("/<int:idUser>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER,UserRole.USER)
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
    @requireRole(UserRole.ADMIN)
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
    @requireRole(UserRole.ADMIN, UserRole.MANAGER, UserRole.USER)
    def updateUser(idUser: int):
        """
        Modifier les informations personnelles d'un utilisateur.
        ---
        tags:
          - Users
        description: Un utilisateur ou un gestionnaire authentifié peut modifier uniquement son propre compte. Un administrateur peut modifier n'importe quel compte. Le rôle ne peut pas être modifié sur cette route.
        security:
          - Bearer: []
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
            description: Informations personnelles modifiées.
            schema:
              $ref: '#/definitions/User'
          400:
            description: Corps invalide, champ non autorisé (dont role) ou informations personnelles invalides.
            schema:
              $ref: '#/definitions/Error'
          401:
            description: Jeton d'authentification manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          403:
            description: Rôle insuffisant ou tentative de modifier le compte d'un autre utilisateur sans être administrateur.
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
        currentUser = g.currentUser
        if currentUser.idUser != idUser and currentUser.role != UserRole.ADMIN:
            return jsonify(
                {"error": "Vous ne pouvez modifier que votre propre compte."}
            ), 403

        user = userService.updateUser(
            idUser, request.get_json(silent=True)
        )
        return jsonify(user.toPublicDict()), 200

    @blueprint.put("/<int:idUser>/role")
    @requireRole(UserRole.ADMIN)
    def updateUserRole(idUser: int):
        """
        Modifier le rôle d'un utilisateur.
        ---
        tags:
          - Users
        description: Réservé aux administrateurs. Un administrateur ne peut pas modifier son propre rôle.
        security:
          - Bearer: []
        consumes:
          - application/json
        parameters:
          - name: idUser
            in: path
            type: integer
            required: true
            description: Identifiant de l'utilisateur cible.
          - in: body
            name: role
            required: true
            schema:
              $ref: '#/definitions/UserRoleInput'
        responses:
          200:
            description: Rôle modifié.
            schema:
              $ref: '#/definitions/User'
          400:
            description: Corps invalide ou rôle qui ne correspond pas à une valeur de UserRole.
            schema:
              $ref: '#/definitions/Error'
          401:
            description: Jeton d'authentification manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          403:
            description: Seul un administrateur peut modifier le rôle d'un autre utilisateur; l'auto-modification est interdite.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Utilisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        currentUser = g.currentUser
        if currentUser.idUser == idUser:
            return jsonify(
                {"error": "Vous ne pouvez pas modifier votre propre rôle."}
            ), 403

        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {"role"}:
            raise InvalidRequestError(
                "The request body must contain only the role field."
            )

        user = userService.updateUserRole(idUser, data["role"])
        return jsonify(user.toPublicDict()), 200

    @blueprint.delete("/<int:idUser>")
    @requireRole(UserRole.ADMIN)
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
