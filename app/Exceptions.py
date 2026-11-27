class NotFoundError(Exception):
    """Classe qui représente une ressource introuvable."""


class AlreadyExistsError(Exception):
    """Classe qui représente une ressource déjà existante."""


class ConflictError(Exception):
    """Classe qui représente un conflit avec l'état actuel des ressources."""


class InvalidReferenceError(Exception):
    """Classe qui représente une référence invalide ou absente."""


class InvalidRequestError(Exception):
    """Classe qui représente une requête invalide ou incomplète."""


class AuthenticationError(Exception):
    """Classe qui représente un échec d'authentification."""


class UserInputError(Exception):
    """Classe qui représente une donnée utilisateur invalide."""

    def __init__(self, message: str):
        super().__init__(message)