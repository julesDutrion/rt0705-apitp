from enum import Enum


class LoanStatus(Enum):
    IN_PROGRESS = ("IN_PROGRESS", "En cours")
    OVERDUE = ("OVERDUE", "En retard")
    RETURNED = ("RETURNED", "Retourné")

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def label(self) -> str:
        return self.value[1]
