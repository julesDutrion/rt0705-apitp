from enum import Enum

class UserRole(Enum):
    """Classe qui représente les rôles attribuables aux utilisateurs."""

    USER = "consulteur"
    MANAGER = "manager"
    ADMIN = "adminstrateur"