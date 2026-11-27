import pytest
from flask import Flask, abort

from app.ErrorHandlers import registerErrorHandlers
from app.Exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    ConflictError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
    UserInputError,
)


@pytest.mark.parametrize(
    ("errorType", "expectedStatus"),
    [
        (InvalidRequestError, 400),
        (UserInputError, 400),
        (AuthenticationError, 401),
        (NotFoundError, 404),
        (AlreadyExistsError, 409),
        (ConflictError, 409),
        (InvalidReferenceError, 422),
    ],
)
def test_business_errors_are_returned_as_json(errorType, expectedStatus):
    app = Flask(__name__)
    app.config["TESTING"] = True
    registerErrorHandlers(app)

    @app.get("/")
    def raiseBusinessError():
        raise errorType("expected error")

    response = app.test_client().get("/")

    assert response.status_code == expectedStatus
    assert response.json == {"error": "expected error"}


def test_http_errors_keep_their_status_and_unexpected_errors_are_sanitized():
    app = Flask(__name__)
    app.config["TESTING"] = True
    registerErrorHandlers(app)

    @app.get("/http")
    def raiseHttpError():
        abort(418, description="teapot")

    @app.get("/unexpected")
    def raiseUnexpectedError():
        raise RuntimeError("internal detail")

    client = app.test_client()
    httpResponse = client.get("/http")
    unexpectedResponse = client.get("/unexpected")

    assert httpResponse.status_code == 418
    assert httpResponse.json == {"error": "teapot"}
    assert unexpectedResponse.status_code == 500
    assert unexpectedResponse.json == {"error": "Internal server error"}
