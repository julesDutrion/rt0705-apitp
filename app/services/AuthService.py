
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
    """Classe qui représente le service d'authentification des utilisateurs."""

    TOKEN_DURATION = timedelta(hours=1)
    JWT_ALGORITHM = "HS256"

    def __init__(self, userDAO: UserDAO) -> None:
        self._userDAO = userDAO
        self._secretKey = os.getenv("JWT_SECRET_KEY")
        if not self._secretKey:
            raise RuntimeError("JWT_SECRET_KEY is not configured.")

    # --- Authentification -----------------------------------------------

    def authenticate(self, login: str, password: str) -> UserDTO:
        """
        Méthode qui authentifie un utilisateur avec son login et son mot de passe.

        :param login: Login de l'utilisateur.
        :param password: Mot de passe fourni.
        :return: DTO de l'utilisateur authentifié.
        :raises InvalidRequestError: Si le login ou le mot de passe est absent.
        :raises AuthenticationError: Si les identifiants sont incorrects.
        """
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
        """
        Méthode qui génère un jeton JWT pour un utilisateur.

        :param user: Utilisateur à authentifier.
        :return: Jeton JWT signé.
        """
        now = datetime.now(timezone.utc)
        payload = {"sub": str(user.idUser), "iat": now, "exp": now + self.TOKEN_DURATION}
        return jwt.encode(
            payload,
            self._secretKey,
            algorithm=self.JWT_ALGORITHM
        )

    # --- Vérification du token ------------------------------------------

    def verifyToken(self, token: str) -> UserDTO:
        """
        Méthode qui valide un jeton JWT et récupère son utilisateur.

        :param token: Jeton JWT à vérifier.
        :return: DTO de l'utilisateur associé.
        :raises InvalidRequestError: Si le jeton ou les données du compte sont invalides.
        :raises NotFoundError: Si l'utilisateur associé n'existe pas.
        """
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
