from datetime import date
from typing import Any
import re
import bcrypt

from pymongo.errors import DuplicateKeyError

from ..dao import UserDAO
from ..Exceptions import (
    AlreadyExistsError,
    InvalidRequestError,
    NotFoundError,
    UserInputError
)
from ..models import UserDTO, UserRole


DEFAULT_ROLE = UserRole.USER

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
)


class UserService:

    def __init__(self, userDAO: UserDAO) -> None:
        self._userDAO = userDAO

    # --- Création ---------------------------------------------------------

    def createUser(self, data: Any) -> UserDTO:
        try:
            user = self._createUserAndHashPassword(data)
            return self._userDAO.create(user)
        except DuplicateKeyError:
            raise AlreadyExistsError(
                "Ce login ou cette adresse e-mail est déjà utilisé."
            )

    # --- Récupération -----------------------------------------------------

    def getUserById(self, idUser: int) -> UserDTO:
        user = self._userDAO.getById(idUser)
        if user is None:
            raise NotFoundError(f"User {idUser} not found")
        return user

    def getUserByLogin(self, login: str) -> UserDTO:
        user = self._userDAO.getByLogin(login)
        if user is None:
            raise NotFoundError(f"User {login} not found")
        return user

    # --- Modification -----------------------------------------------------

    def updateUser(self, idUser: int, data: Any) -> UserDTO:
        if not isinstance(data, dict):
            raise InvalidRequestError("Invalid request body.")
        if "idUser" in data and data["idUser"] != idUser:
            raise InvalidRequestError(
                "idUser in the URL and in the body must match."
            )
        user = self.getUserById(idUser)
        login = data.get("login", user.login)
        email = data.get("email", user.email)
        login = login.strip() if isinstance(login, str) else login
        email = email.strip() if isinstance(email, str) else email
        self._validateLogin(login, idUser)
        self._validateEmail(email, idUser)
        user.login = login
        user.email = email
        if "birthDate" in data:
            try:
                parsedBirthDate = date.fromisoformat(data["birthDate"])
            except (ValueError, TypeError):
                raise UserInputError(
                    "La date de naissance est invalide."
                )
            if parsedBirthDate > date.today():
                raise UserInputError(
                    "La date de naissance ne peut pas être dans le futur."
                )
            user.birthDate = parsedBirthDate
        if "password" in data and data["password"]:
            self._validatePassword(data["password"])
            user.passwordHash = bcrypt.hashpw(
                data["password"].encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")
        try:
            if not self._userDAO.update(user):
                raise NotFoundError(f"User {idUser} not found")
        except DuplicateKeyError:
            raise AlreadyExistsError(
                "Ce login ou cette adresse e-mail est déjà utilisé."
            )
        return user

    # --- Suppression ------------------------------------------------------

    def deleteUser(self, idUser: int) -> None:
        if not self._userDAO.delete(idUser):
            raise NotFoundError(f"User {idUser} not found")

    # --- Validations ------------------------------------------------------

    def _validatePassword(self, password: str) -> None:
        if not isinstance(password, str) or not PASSWORD_REGEX.fullmatch(password):
            raise UserInputError(
                "Le mot de passe doit contenir une minuscule, "
                "une majuscule, un chiffre et un symbole, "
                "et comporter au moins 12 caractères."
            )

        if len(password.encode("utf-8")) > 72:
            raise UserInputError(
                "Le mot de passe ne doit pas dépasser 72 octets."
            )

    def _validateLogin(self, login: str, excludeUserId: int = None) -> None:
        if not isinstance(login, str) or not login.strip():
            raise UserInputError("Le login est invalide.")
        existingUser = self._userDAO.getByLogin(login)
        if existingUser and existingUser.idUser != excludeUserId:
            raise UserInputError("Ce login est déjà utilisé.")

    def _validateEmail(self, email: str, excludeUserId: int = None) -> None:
        if email is None:
            raise UserInputError(
                "L'adresse e-mail est obligatoire."
            )
        if not isinstance(email, str) or not email.strip():
            raise UserInputError(
                "L'adresse e-mail est invalide."
            )
        existingUser = self._userDAO.getByEmail(email)
        if existingUser and existingUser.idUser != excludeUserId:
            raise UserInputError(
                "Cette adresse e-mail est déjà utilisée."
            )

    # --- Construction du DTO ---------------------------------------------

    def _createUserAndHashPassword(self, data: Any) -> UserDTO:
        if not isinstance(data, dict):
            raise InvalidRequestError("Invalid request body.")
        login = data.get("login")
        email = data.get("email")
        password = data.get("password")
        birthDate = data.get("birthDate")
        login = login.strip() if isinstance(login, str) else login
        email = email.strip() if isinstance(email, str) else email
        self._validatePassword(password)
        self._validateLogin(login)
        self._validateEmail(email)
        try:
            parsedBirthDate = date.fromisoformat(birthDate)
        except (ValueError, TypeError):
            raise UserInputError(
                "La date de naissance est invalide."
            )
        if parsedBirthDate > date.today():
            raise UserInputError(
                "La date de naissance ne peut pas être dans le futur."
            )
        passwordHash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")
        return UserDTO(
            role=DEFAULT_ROLE,
            login=login,
            email=email,
            passwordHash=passwordHash,
            birthDate=parsedBirthDate
        )