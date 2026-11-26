from flask import Blueprint, jsonify, request

from ..Exceptions import InvalidRequestError
from ..services import AuthService


def createAuthBlueprint(authService: AuthService) -> Blueprint:
    blueprint = Blueprint("auth", __name__, url_prefix="/auth")

    @blueprint.post("/login")
    def login():
        """
        Se connecter et obtenir un jeton JWT.
        ---
        tags:
          - Authentication
        description: Cette route est publique. Utiliser le jeton retourné dans l'en-tête Authorization sous la forme « Bearer <JWT> ».
        security: []
        consumes:
          - application/json
        parameters:
          - in: body
            name: credentials
            required: true
            schema:
              $ref: '#/definitions/LoginInput'
        responses:
          200:
            description: Authentification réussie.
            schema:
              $ref: '#/definitions/LoginResponse'
          400:
            description: Corps JSON invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          401:
            description: Login ou mot de passe incorrect.
            schema:
              $ref: '#/definitions/Error'
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {"login", "password"}:
            raise InvalidRequestError(
                "The request body must contain only login and password."
            )

        user = authService.authenticate(data["login"], data["password"])
        token = authService.generateToken(user)
        return jsonify({
            "accessToken": token,
            "tokenType": "Bearer",
            "expiresIn": int(authService.TOKEN_DURATION.total_seconds()),
            "user": user.toPublicDict(),
        }), 200

    return blueprint
