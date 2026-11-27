
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from ..dao import UserDAO
from ..models import UserDTO
from ..Exceptions import (
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
)


class AuthService:

    TOKEN_DURATION = timedelta(hours=1)
    JWT_ALGORITHM = "HS256"

    def __init__(self, userDAO: UserDAO) -> None:
        self._userDAO = userDAO
        self._secretKey = os.getenv("JWT_SECRET_KEY")
        if not self._secretKey:
            raise RuntimeError("JWT_SECRET_KEY is not configured.")

    # --- Authentification -----------------------------------------------

    def authenticate(self, login: str, password: str) -> UserDTO:
        if (
            not isinstance(login, str)
            or not login.strip()
            or not isinstance(password, str)
            or not password
        ):
            raise InvalidRequestError("Login and password are required.")

        user = self._userDAO.getByLogin(login.strip())
        if user is None:
            raise AuthenticationError("Identifiants incorrects.")
        passwordBytes = password.encode("utf-8")
        if len(passwordBytes) > 72:
            raise AuthenticationError("Identifiants incorrects.")
        if not bcrypt.checkpw(
            passwordBytes,
            user.passwordHash.encode("utf-8")
        ):
            raise AuthenticationError("Identifiants incorrects.")

        return user

    # --- Génération du token --------------------------------------------

    def generateToken(self, user: UserDTO) -> str:
        now = datetime.now(timezone.utc)
        payload = {"sub": str(user.idUser), "iat": now, "exp": now + self.TOKEN_DURATION}
        return jwt.encode(
            payload,
            self._secretKey,
            algorithm=self.JWT_ALGORITHM
        )

    # --- Vérification du token ------------------------------------------

    def verifyToken(self, token: str) -> UserDTO:
        try:
            payload = jwt.decode(
                token,
                self._secretKey,
                algorithms=[self.JWT_ALGORITHM]
            )

            idUser = int(payload["sub"])

        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            raise InvalidRequestError("Session invalide ou expiré.")

        try:
            user = self._userDAO.getById(idUser)
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidRequestError(
                "Les informations du compte sont invalides."
            ) from error

        if user is None:
            raise NotFoundError("Utilisateur introuvable.")

        return user
