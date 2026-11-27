from enum import Enum


class LoanStatus(Enum):
    """Classe qui représente les statuts possibles d'un emprunt."""

    IN_PROGRESS = ("IN_PROGRESS", "En cours")
    OVERDUE = ("OVERDUE", "En retard")
    RETURNED = ("RETURNED", "Retourné")

    @property
    def code(self) -> str:
        """
        Méthode qui retourne le code du statut.

        :return: Code de statut destiné aux échanges avec le client.
        """
        return self.value[0]

    @property
    def label(self) -> str:
        """
        Méthode qui retourne le libellé français du statut.

        :return: Libellé du statut.
        """
        return self.value[1]
