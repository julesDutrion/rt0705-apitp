from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError

from ..dao import LoanDAO, SupportDAO, UserDAO
from ..Exceptions import (
    ConflictError,
    InvalidReferenceError,
    InvalidRequestError,
    NotFoundError,
)
from ..models import LoanDTO, SupportDTO
from .FilmService import FilmService


LOAN_DURATION_DAYS = 30


class LoanService:
    """Classe qui représente le service de gestion des emprunts."""

    def __init__(
        self,
        loanDAO: LoanDAO,
        userDAO: UserDAO,
        supportDAO: SupportDAO,
        filmService: FilmService,
    ) -> None:
        self._loanDAO = loanDAO
        self._userDAO = userDAO
        self._supportDAO = supportDAO
        self._filmService = filmService

    def borrow(self, idUser: int, data: Any) -> LoanDTO:
        """
        Méthode qui crée un emprunt pour un utilisateur.

        :param idUser: Identifiant de l'utilisateur authentifié.
        :param data: Données identifiant le support à emprunter.
        :return: DTO de l'emprunt créé.
        :raises InvalidRequestError: Si les données de l'emprunt sont invalides.
        :raises NotFoundError: Si l'utilisateur ou le support n'existe pas.
        :raises InvalidReferenceError: Si le support n'est pas physique.
        :raises ConflictError: Si le support possède déjà un emprunt actif.
        """
        if not isinstance(data, dict) or set(data) != {"idPhysicalSupport"}:
            raise InvalidRequestError(
                "The request body must contain only idPhysicalSupport."
            )
        idPhysicalSupport = data["idPhysicalSupport"]
        if (
            not isinstance(idPhysicalSupport, int)
            or isinstance(idPhysicalSupport, bool)
            or idPhysicalSupport < 1
        ):
            raise InvalidRequestError(
                "idPhysicalSupport must be a positive integer."
            )
        if not self._userDAO.exists(idUser):
            raise NotFoundError(f"User {idUser} not found")

        support = self._supportDAO.getById(idPhysicalSupport)
        if support is None:
            raise NotFoundError(
                f"Physical support {idPhysicalSupport} not found"
            )
        if support.supportType is None or support.supportType.mode != "physical":
            raise InvalidReferenceError(
                f"Support {idPhysicalSupport} is not physical"
            )
        self._filmService.getFilmForUser(support.idFilm, idUser)
        if self._loanDAO.hasActiveLoanForSupport(idPhysicalSupport):
            raise ConflictError(
                f"Physical support {idPhysicalSupport} is already borrowed"
            )

        startDate = datetime.now(timezone.utc)
        loan = LoanDTO(
            idLoan=self._loanDAO.nextId(),
            idUser=idUser,
            idPhysicalSupport=idPhysicalSupport,
            startDate=startDate,
            expectedReturnDate=startDate
            + timedelta(days=LOAN_DURATION_DAYS),
        )
        try:
            return self._loanDAO.create(loan)
        except DuplicateKeyError as error:
            raise ConflictError(
                f"Physical support {idPhysicalSupport} is already borrowed"
            ) from error

    def getLoansForUser(self, idUser: int) -> List[LoanDTO]:
        """
        Méthode qui récupère les emprunts d'un utilisateur.

        :param idUser: Identifiant de l'utilisateur.
        :return: Liste des DTO d'emprunts.
        """
        return self._loanDAO.getByUserId(idUser)

    def getLoansForUserByLogin(self, login: str) -> List[LoanDTO]:
        """
        Méthode qui récupère les emprunts d'un utilisateur par son login.

        :param login: Login de l'utilisateur recherché.
        :return: Liste des DTO d'emprunts.
        :raises InvalidRequestError: Si le login est vide ou invalide.
        :raises NotFoundError: Si l'utilisateur n'existe pas.
        """
        if not isinstance(login, str) or not login.strip():
            raise InvalidRequestError("login must be a non-empty string.")
        user = self._userDAO.getByLogin(login.strip())
        if user is None:
            raise NotFoundError(f"User {login} not found")
        return self._loanDAO.getByUserId(user.idUser)

    def getLoanForUser(self, idLoan: int, idUser: int) -> LoanDTO:
        """
        Méthode qui récupère un emprunt appartenant à un utilisateur.

        :param idLoan: Identifiant de l'emprunt.
        :param idUser: Identifiant du propriétaire.
        :return: DTO de l'emprunt.
        :raises NotFoundError: Si l'emprunt n'appartient pas à l'utilisateur.
        """
        loan = self._loanDAO.getByIdAndUserId(idLoan, idUser)
        if loan is None:
            raise NotFoundError(f"Loan {idLoan} not found")
        return loan

    def getAllLoans(self) -> List[LoanDTO]:
        """
        Méthode qui récupère tous les emprunts.

        :return: Liste des DTO d'emprunts.
        """
        return self._loanDAO.getAll()

    def getLoanById(self, idLoan: int) -> LoanDTO:
        """
        Méthode qui récupère un emprunt par son identifiant.

        :param idLoan: Identifiant de l'emprunt.
        :return: DTO de l'emprunt.
        :raises NotFoundError: Si l'emprunt n'existe pas.
        """
        loan = self._loanDAO.getById(idLoan)
        if loan is None:
            raise NotFoundError(f"Loan {idLoan} not found")
        return loan

    def toPublicDict(self, loan: LoanDTO) -> Dict[str, Any]:
        """
        Méthode qui prépare les données publiques d'un emprunt.

        :param loan: DTO de l'emprunt.
        :return: Données de l'emprunt destinées au client.
        """
        support = self._supportDAO.getById(loan.idPhysicalSupport)
        return self._serializeLoan(loan, support)

    def toPublicDicts(
        self, loans: List[LoanDTO]
    ) -> List[Dict[str, Any]]:
        """
        Méthode qui prépare les données publiques de plusieurs emprunts.

        :param loans: Emprunts à convertir.
        :return: Liste des données d'emprunts destinées au client.
        """
        supportIds = {loan.idPhysicalSupport for loan in loans}
        supportsById = {
            support.idSupport: support
            for support in self._supportDAO.getByIds(supportIds)
        }
        return [
            self._serializeLoan(
                loan, supportsById.get(loan.idPhysicalSupport)
            )
            for loan in loans
        ]

    def returnLoan(self, idLoan: int) -> LoanDTO:
        """
        Méthode qui enregistre le retour d'un emprunt actif.

        :param idLoan: Identifiant de l'emprunt à retourner.
        :return: DTO de l'emprunt retourné.
        :raises NotFoundError: Si l'emprunt n'existe pas.
        :raises ConflictError: Si l'emprunt a déjà été retourné.
        """
        now = datetime.now(timezone.utc)
        returnedLoan = self._loanDAO.markReturned(idLoan, now)
        if returnedLoan is not None:
            return returnedLoan
        if self._loanDAO.getById(idLoan) is None:
            raise NotFoundError(f"Loan {idLoan} not found")
        raise ConflictError(f"Loan {idLoan} has already been returned")

    @staticmethod
    def _serializeLoan(
        loan: LoanDTO, support: Optional[SupportDTO]
    ) -> Dict[str, Any]:
        data = loan.toPublicDict()
        data["supportType"] = (
            support.supportType.toDict()
            if support is not None and support.supportType is not None
            else None
        )
        return data
