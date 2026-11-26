class NotFoundError(Exception):
    """Aucune entité ne correspond à la demande."""


class AlreadyExistsError(Exception):
    """Une entité avec le même identifiant existe déjà."""


class ConflictError(Exception):
    """Une opération compromettrait la cohérence des références."""


class InvalidReferenceError(Exception):
    """Une entité référencée (réalisateur, genre, langue...) n'existe pas."""


class InvalidRequestError(Exception):
    """Le corps de la requête est absent, malformé ou incomplet."""


class AuthenticationError(Exception):
    """Les identifiants d'authentification sont incorrects."""


class UserInputError(Exception):
    """Erreur liée aux informations saisies par l'utilisateur."""

    def __init__(self, message: str):
        super().__init__(message)