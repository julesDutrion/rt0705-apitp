"""Traduction des exceptions en réponses HTTP (JSON)."""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from Exceptions import (
    AlreadyExistsError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
)


def registerErrorHandlers(app: Flask) -> None:
    # --- Exceptions métier ------------------------------------------------
    @app.errorhandler(InvalidRequestError)
    def handleInvalidRequest(error: InvalidRequestError):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(NotFoundError)
    def handleNotFound(error: NotFoundError):
        return jsonify({"error": str(error)}), 404

    @app.errorhandler(AlreadyExistsError)
    def handleAlreadyExists(error: AlreadyExistsError):
        return jsonify({"error": str(error)}), 409

    @app.errorhandler(InvalidReferenceError)
    def handleInvalidReference(error: InvalidReferenceError):
        return jsonify({"error": str(error)}), 422

    # --- Erreurs HTTP de Flask (route inconnue, méthode non autorisée...) --
    @app.errorhandler(HTTPException)
    def handleHttpException(error: HTTPException):
        return jsonify({"error": error.description}), error.code

    # --- Erreurs imprévues (bug, base MongoDB injoignable...) -------------
    @app.errorhandler(Exception)
    def handleUnexpectedError(error: Exception):
        app.logger.exception("Unhandled exception")  # trace complète dans les logs
        return jsonify({"error": "Internal server error"}), 500