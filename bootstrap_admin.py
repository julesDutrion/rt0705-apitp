
import getpass
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError


# ==================================================
# Configuration
# ==================================================

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_BOOTSTRAP_HOST", "127.0.0.1")
MONGO_PORT = os.getenv("MONGO_HOST_PORT", "27017")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "videotheque")
MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE", "admin")

ADMIN_LOGIN = "admin"

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
)


# ==================================================
# Saisie des informations
# ==================================================

def askEmail() -> str:
    while True:
        email = input("Adresse e-mail de l'administrateur : ").strip()

        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return email

        print("Adresse e-mail invalide.")


def askBirthDate() -> date:
    while True:
        value = input("Date de naissance (AAAA-MM-JJ) : ").strip()

        try:
            birthDate = date.fromisoformat(value)

            if birthDate > date.today():
                print("La date de naissance ne peut pas être dans le futur.")
                continue

            return birthDate

        except ValueError:
            print("Format invalide. Exemple : 2000-05-21.")


def askPassword() -> str:
    while True:
        password = getpass.getpass("Mot de passe administrateur : ")

        if not PASSWORD_REGEX.fullmatch(password):
            print(
                "Le mot de passe doit contenir au moins 12 caractères, "
                "une minuscule, une majuscule, un chiffre et un symbole."
            )
            continue

        if len(password.encode("utf-8")) > 72:
            print("Le mot de passe dépasse la limite de 72 octets de bcrypt.")
            continue

        confirmation = getpass.getpass("Confirmer le mot de passe : ")

        if password != confirmation:
            print("Les mots de passe ne correspondent pas.")
            continue

        return password


# ==================================================
# Création du compte administrateur
# ==================================================

def createAdmin(userDAO) -> None:
    from app.models import UserDTO, UserRole

    existingUser = userDAO.getByLogin(ADMIN_LOGIN)

    if existingUser is not None:
        print(
            "Un compte avec le login 'admin' existe déjà. "
            "Le bootstrap est refusé."
        )
        raise SystemExit(1)

    print("\nCréation du compte administrateur.")

    email = askEmail()

    if userDAO.getByEmail(email) is not None:
        raise ValueError("Cette adresse e-mail est déjà utilisée.")

    birthDate = askBirthDate()
    password = askPassword()

    passwordHash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    admin = UserDTO(
        role=UserRole.ADMIN,
        login=ADMIN_LOGIN,
        email=email,
        passwordHash=passwordHash,
        birthDate=birthDate
    )

    try:
        userDAO.create(admin)
    except DuplicateKeyError:
        raise ValueError(
            "Le login ou l'adresse e-mail est déjà utilisé."
        )

    print("\nCompte administrateur créé avec succès.")
    print(f"Login : {ADMIN_LOGIN}")


# ==================================================
# Point d'entrée
# ==================================================

def main() -> None:
    if not MONGO_USERNAME or not MONGO_PASSWORD:
        raise RuntimeError(
            "Identifiants MongoDB absents du fichier .env."
        )

    # L'API utilise le nom DNS "mongodb" dans Docker.
    # Le bootstrap tourne sur l'hôte et utilise donc 127.0.0.1.
    #
    # On positionne ces variables avant l'import du package app,
    # car app.config.database lit la configuration à son import.
    os.environ["MONGO_HOST"] = MONGO_HOST
    os.environ["MONGO_PORT"] = MONGO_PORT

    from app.dao import UserDAO

    username = quote_plus(MONGO_USERNAME)
    password = quote_plus(MONGO_PASSWORD)

    mongoURI = (
        f"mongodb://{username}:{password}"
        f"@{MONGO_HOST}:{MONGO_PORT}/"
        f"{MONGO_DATABASE}?authSource={MONGO_AUTH_SOURCE}"
    )

    client = MongoClient(
        mongoURI,
        serverSelectionTimeoutMS=5000
    )

    try:
        client.admin.command("ping")

        database = client[MONGO_DATABASE]
        userDAO = UserDAO(database)

        createAdmin(userDAO)

    finally:
        client.close()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, PyMongoError) as error:
        print(f"\nErreur lors du bootstrap administrateur : {error}")
        sys.exit(1)
