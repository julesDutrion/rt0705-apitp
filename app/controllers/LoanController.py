from flask import Blueprint, g, jsonify, request

from ..decorators import requireRole
from ..models import UserRole
from ..services import LoanService


def createLoanBlueprint(loanService: LoanService) -> Blueprint:
    blueprint = Blueprint("loans", __name__, url_prefix="/loans")

    @blueprint.post("")
    @requireRole(UserRole.USER, UserRole.MANAGER, UserRole.ADMIN)
    def borrowSupport():
        """
        Emprunter un support physique disponible.
        ---
        tags:
          - Loans
        consumes:
          - application/json
        parameters:
          - in: body
            name: loan
            required: true
            schema:
              $ref: '#/definitions/LoanInput'
        responses:
          201:
            description: Emprunt créé.
            schema:
              $ref: '#/definitions/Loan'
          400:
            description: Corps invalide.
            schema:
              $ref: '#/definitions/Error'
          401:
            description: Jeton manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Utilisateur ou support introuvable.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Support déjà emprunté.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Le support demandé n'est pas physique.
            schema:
              $ref: '#/definitions/Error'
        """
        loan = loanService.borrow(
            g.currentUser.idUser, request.get_json(silent=True)
        )
        return jsonify(loanService.toPublicDict(loan)), 201

    @blueprint.get("/me")
    @requireRole(UserRole.USER, UserRole.MANAGER, UserRole.ADMIN)
    def getMyLoans():
        """
        Lister les emprunts de l'utilisateur authentifié.
        ---
        tags:
          - Loans
        responses:
          200:
            description: Emprunts personnels avec leur état calculé.
            schema:
              type: array
              items:
                $ref: '#/definitions/Loan'
          401:
            description: Jeton manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
        """
        loans = loanService.getLoansForUser(g.currentUser.idUser)
        return jsonify(loanService.toPublicDicts(loans)), 200

    @blueprint.get("/me/<int:idLoan>")
    @requireRole(UserRole.USER, UserRole.MANAGER, UserRole.ADMIN)
    def getMyLoan(idLoan: int):
        """
        Récupérer un emprunt appartenant à l'utilisateur authentifié.
        ---
        tags:
          - Loans
        parameters:
          - name: idLoan
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Détail de l'emprunt personnel.
            schema:
              $ref: '#/definitions/Loan'
          401:
            description: Jeton manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Emprunt introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        loan = loanService.getLoanForUser(idLoan, g.currentUser.idUser)
        return jsonify(loanService.toPublicDict(loan)), 200

    @blueprint.get("")
    @requireRole(UserRole.MANAGER, UserRole.ADMIN)
    def getAllLoans():
        """
        Lister tous les emprunts (manager ou administrateur).
        ---
        tags:
          - Loans
        responses:
          200:
            description: Liste des emprunts avec leur état calculé.
            schema:
              type: array
              items:
                $ref: '#/definitions/Loan'
          401:
            description: Jeton manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          403:
            description: Rôle insuffisant.
            schema:
              $ref: '#/definitions/Error'
        """
        loans = loanService.getAllLoans()
        return jsonify(loanService.toPublicDicts(loans)), 200

    @blueprint.get("/user/<string:login>")
    @requireRole(UserRole.MANAGER, UserRole.ADMIN)
    def getLoansByUserLogin(login: str):
        """
        Rechercher les emprunts d'un utilisateur par son login.
        Réservé aux managers et aux administrateurs.
        ---
        tags:
          - Loans
        parameters:
          - name: login
            in: path
            type: string
            required: true
        responses:
          200:
            description: Emprunts associés au login, avec le type de support.
            schema:
              type: array
              items:
                $ref: '#/definitions/Loan'
          401:
            description: Jeton manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          403:
            description: Réservé aux managers et administrateurs.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Utilisateur introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        loans = loanService.getLoansForUserByLogin(login)
        return jsonify(loanService.toPublicDicts(loans)), 200

    @blueprint.get("/<int:idLoan>")
    @requireRole(UserRole.MANAGER, UserRole.ADMIN)
    def getLoan(idLoan: int):
        """
        Récupérer un emprunt par son identifiant (manager ou administrateur).
        ---
        tags:
          - Loans
        parameters:
          - name: idLoan
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Emprunt trouvé.
            schema:
              $ref: '#/definitions/Loan'
          401:
            description: Jeton manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          403:
            description: Rôle insuffisant.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Emprunt introuvable.
            schema:
              $ref: '#/definitions/Error'
        """
        loan = loanService.getLoanById(idLoan)
        return jsonify(loanService.toPublicDict(loan)), 200

    @blueprint.patch("/<int:idLoan>/return")
    @requireRole(UserRole.MANAGER, UserRole.ADMIN)
    def returnLoan(idLoan: int):
        """
        Enregistrer le retour d'un emprunt (manager ou administrateur).
        ---
        tags:
          - Loans
        parameters:
          - name: idLoan
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Emprunt retourné et support rendu disponible.
            schema:
              $ref: '#/definitions/Loan'
          401:
            description: Jeton manquant, invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          403:
            description: Rôle insuffisant.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Emprunt introuvable.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Emprunt déjà retourné.
            schema:
              $ref: '#/definitions/Error'
        """
        loan = loanService.returnLoan(idLoan)
        return jsonify(loanService.toPublicDict(loan)), 200

    return blueprint
