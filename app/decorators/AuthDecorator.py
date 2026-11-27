
from functools import wraps
from flask import current_app, g, jsonify, request

from ..Exceptions import InvalidRequestError, NotFoundError


def optionalAuth(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        authHeader = request.headers.get("Authorization")
        if not authHeader:
            g.currentUser = None
            return function(*args, **kwargs)

        if not authHeader.startswith("Bearer "):
            return jsonify({"error": "Token invalide ou expiré."}), 401

        token = authHeader.split(" ", 1)[1]
        authService = current_app.extensions["authService"]
        try:
            g.currentUser = authService.verifyToken(token)
        except (InvalidRequestError, NotFoundError):
            return jsonify({"error": "Token invalide ou expiré."}), 401
        return function(*args, **kwargs)

    return wrapper


def requireRole(*allowedRoles):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):

            authHeader = request.headers.get("Authorization")

            if not authHeader or not authHeader.startswith("Bearer "):
                return jsonify({"error": "Token manquant."}), 401

            token = authHeader.split(" ", 1)[1]

            authService = current_app.extensions["authService"]

            try:
                user = authService.verifyToken(token)
            except (InvalidRequestError, NotFoundError):
                return jsonify({"error": "Token invalide ou expiré."}), 401

            if user.role not in allowedRoles:
                return jsonify({"error": "Accès interdit."}), 403

            g.currentUser = user
            return function(*args, **kwargs)

        return wrapper

    return decorator
