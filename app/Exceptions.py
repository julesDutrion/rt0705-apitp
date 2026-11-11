class NotFoundError(Exception):
    """Aucune entité ne correspond à la demande."""


class AlreadyExistsError(Exception):
    """Une entité avec le même identifiant existe déjà."""