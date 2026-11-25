from typing import List

from pymongo.errors import DuplicateKeyError

from ..dao import UserDAO
from ..Exceptions import AlreadyExistsError, NotFoundError, UserInputError
from ..models import UserDTO
import re
import bcrypt

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
)
class UserService:

    def __init__(self, userDAO: UserDAO) -> None: self._userDAO = userDAO

    def createActor(self, user: UserDTO) -> UserDTO:
            try:
                self._validatePassword(user.passwordHash)
                self._validateEmail(user.email)
                self._validateLogin(user.login)
                user.passwordHash = bcrypt.hashpw(
                    user.passwordHash.encode("utf-8"),
                    bcrypt.gensalt()
                ).decode("utf-8")
                return self._actorDAO.create(user)
            except DuplicateKeyError:
                raise AlreadyExistsError(f"User {user.idUser} already exists")

    def _validatePassword(self, password : str) -> None:
        if not PASSWORD_REGEX.fullmatch(password):
            raise UserInputError("Le mot de passe doit contenir une minuscule, majuscule, un chiffre et un symbole")

    def _validateLogin(self,login :str) -> None:
        if self._userDAO.getByLogin(login):
            raise UserInputError("Ce login est déjà utilisé.")

    def _validateEmail(self, email : str) -> None:
        if (self._userDAO.getByEmail(email)):
            raise UserInputError("Cette adresse mail est déjà utilisée.")

    
            