class NotFoundError(Exception):
    """Aucune entité ne correspond à la demande."""


class AlreadyExistsError(Exception):
    """Une entité avec le même identifiant existe déjà."""


class InvalidReferenceError(Exception):
    """Une entité référencée (réalisateur, genre, langue...) n'existe pas."""


class InvalidRequestError(Exception):
    """Le corps de la requête est absent, malformé ou incomplet."""