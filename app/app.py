"""Racine de composition : assemble les dépendances et crée l'application Flask."""

import os

from flask import Flask
from flasgger import Swagger
from pymongo import MongoClient

from .config.database import database as DATABASE_NAME
from .config.database import uri as MONGO_URI

from .controllers import (
    createActorBlueprint,
    createClassificationBlueprint,
    createDirectorBlueprint,
    createFilmBlueprint,
    createGenreBlueprint,
    createLanguageBlueprint,
    createSupportBlueprint,
    createSupportTypeBlueprint,
)

'''Listes des daos'''
from .dao import (
    ActorDAO,
    ClassificationDAO,
    DirectorDAO,
    FilmDAO,
    GenreDAO,
    LanguageDAO,
    SupportDAO,
    SupportTypeDAO,
)

'''Listes des services'''
from .services import (
    ActorService,
    ClassificationService,
    DirectorService,
    FilmService,
    GenreService,
    LanguageService,
    SupportService,
    SupportTypeService,
)

from .ErrorHandlers import registerErrorHandlers

def createApp() -> Flask:
    app = Flask(__name__)

    # Documentation interactive de l'API (désactivable avec SWAGGER_ENABLED=false).
    if os.getenv("SWAGGER_ENABLED", "true").lower() == "true":
        Swagger(app, template={
            "swagger": "2.0",
            "info": {
                "title": "API Vidéothèque",
                "description": "Documentation des endpoints de l'API de gestion de vidéothèque.",
                "version": "1.0.0",
            },
            "definitions": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string", "example": "Resource not found"}
                    },
                },
                "Classification": {
                    "type": "object",
                    "required": ["idClassification", "minAge"],
                    "properties": {
                        "idClassification": {"type": "integer", "example": 1},
                        "minAge": {"type": "integer", "example": 12},
                    },
                },
                "ClassificationInput": {
                    "type": "object",
                    "required": ["minAge"],
                    "properties": {
                        "minAge": {"type": "integer", "example": 12},
                    },
                },
                "Director": {
                    "type": "object",
                    "required": ["idDirector", "lastName", "firstName"],
                    "properties": {
                        "idDirector": {"type": "integer", "example": 1},
                        "lastName": {"type": "string", "example": "Nolan"},
                        "firstName": {"type": "string", "example": "Christopher"},
                    },
                },
                "DirectorInput": {
                    "type": "object",
                    "required": ["lastName", "firstName"],
                    "properties": {
                        "lastName": {"type": "string", "example": "Nolan"},
                        "firstName": {"type": "string", "example": "Christopher"},
                    },
                },
                "Genre": {
                    "type": "object",
                    "required": ["idGenre", "nameGenre"],
                    "properties": {
                        "idGenre": {"type": "integer", "example": 1},
                        "nameGenre": {"type": "string", "example": "Science-fiction"},
                    },
                },
                "GenreInput": {
                    "type": "object",
                    "required": ["nameGenre"],
                    "properties": {
                        "nameGenre": {"type": "string", "example": "Science-fiction"},
                    },
                },
                "Language": {
                    "type": "object",
                    "required": ["idLanguage", "code", "name"],
                    "properties": {
                        "idLanguage": {"type": "integer", "example": 1},
                        "code": {"type": "string", "example": "fr"},
                        "name": {"type": "string", "example": "Français"},
                    },
                },
                "LanguageInput": {
                    "type": "object",
                    "required": ["code", "name"],
                    "properties": {
                        "code": {"type": "string", "example": "fr"},
                        "name": {"type": "string", "example": "Français"},
                    },
                },
                "Actor": {
                    "type": "object",
                    "required": ["idActor", "firstName", "lastName"],
                    "properties": {
                        "idActor": {"type": "integer", "example": 1},
                        "firstName": {"type": "string", "example": "Leonardo"},
                        "lastName": {"type": "string", "example": "DiCaprio"},
                    },
                },
                "ActorInput": {
                    "type": "object",
                    "required": ["firstName", "lastName"],
                    "properties": {
                        "firstName": {"type": "string", "example": "Leonardo"},
                        "lastName": {"type": "string", "example": "DiCaprio"},
                    },
                },
                "Support": {
                    "type": "object",
                    "description": "Un exemplaire physique ou un accès numérique associé à un film.",
                    "required": ["idSupport", "idFilm", "idSupportType"],
                    "properties": {
                        "idSupport": {"type": "integer", "example": 1},
                        "idFilm": {"type": "string", "example": "film-001"},
                        "idSupportType": {"type": "integer", "example": 1},
                        "location": {
                            "type": "string",
                            "example": "Étagère A2",
                            "description": "Présente pour un type physical.",
                        },
                        "url": {
                            "type": "string",
                            "example": "https://example.com/video.mp4",
                            "description": "URL HTTP(S), présente pour un type digital.",
                        },
                        "supportType": {"$ref": "#/definitions/SupportType"},
                    },
                },
                "SupportInput": {
                    "type": "object",
                    "description": "Fournir location pour physical ou url pour digital, selon le mode du type référencé.",
                    "required": ["idFilm", "idSupportType"],
                    "properties": {
                        "idFilm": {"type": "string", "example": "film-001"},
                        "idSupportType": {"type": "integer", "example": 1},
                        "location": {
                            "type": "string",
                            "example": "Étagère A2",
                            "description": "Obligatoire pour physical; interdit pour digital.",
                        },
                        "url": {
                            "type": "string",
                            "example": "https://example.com/video.mp4",
                            "description": "URL HTTP(S), obligatoire pour digital; interdite pour physical.",
                        },
                    },
                },
                "SupportType": {
                    "type": "object",
                    "description": "Type de support disponible pour les films.",
                    "required": ["idSupportType", "name", "mode"],
                    "properties": {
                        "idSupportType": {"type": "integer", "example": 1},
                        "name": {"type": "string", "example": "Blu-ray"},
                        "mode": {
                            "type": "string",
                            "enum": ["physical", "digital"],
                            "description": "Détermine si chaque support requiert location ou url.",
                        },
                    },
                },
                "SupportTypeInput": {
                    "type": "object",
                    "description": "Créer ou remplacer un type de support.",
                    "required": ["name", "mode"],
                    "properties": {
                        "name": {"type": "string", "example": "Blu-ray"},
                        "mode": {
                            "type": "string",
                            "enum": ["physical", "digital"],
                            "description": "physical pour un support localisé; digital pour un accès URL.",
                        },
                    },
                },
                "DirectorReference": {
                    "type": "object",
                    "required": ["idDirector"],
                    "properties": {
                        "idDirector": {"type": "integer", "example": 1},
                    },
                },
                "ClassificationReference": {
                    "type": "object",
                    "required": ["idClassification"],
                    "properties": {
                        "idClassification": {"type": "integer", "example": 1},
                    },
                },
                "LanguageReference": {
                    "type": "object",
                    "required": ["idLanguage"],
                    "properties": {
                        "idLanguage": {"type": "integer", "example": 1},
                    },
                },
                "GenreReference": {
                    "type": "object",
                    "required": ["idGenre"],
                    "properties": {
                        "idGenre": {"type": "integer", "example": 1},
                    },
                },
                "ActorReference": {
                    "type": "object",
                    "required": ["idActor"],
                    "properties": {
                        "idActor": {"type": "integer", "example": 1},
                    },
                },
                "Film": {
                    "type": "object",
                    "required": ["idFilm", "title", "synopsis", "releaseDate", "duration", "posterUrl", "addedDate"],
                    "properties": {
                        "idFilm": {"type": "string", "example": "film-001"},
                        "title": {"type": "string", "example": "Interstellar"},
                        "synopsis": {"type": "string", "example": "Un voyage au-delà de notre système solaire."},
                        "releaseDate": {"type": "string", "format": "date", "example": "2014-11-05"},
                        "duration": {"type": "integer", "example": 169},
                        "posterUrl": {"type": "string", "example": "https://example.com/interstellar.jpg"},
                        "addedDate": {"type": "string", "format": "date", "example": "2026-11-20"},
                        "director": {"$ref": "#/definitions/Director"},
                        "classification": {"$ref": "#/definitions/Classification"},
                        "supports": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/Support"},
                            "description": "Supports associés au film, chargés depuis la collection supports.",
                        },
                        "nativeLanguage": {"$ref": "#/definitions/Language"},
                        "languages": {"type": "array", "items": {"$ref": "#/definitions/Language"}},
                        "genre": {"type": "array", "items": {"$ref": "#/definitions/Genre"}},
                        "actors": {"type": "array", "items": {"$ref": "#/definitions/Actor"}},
                    },
                },
                "FilmInput": {
                    "type": "object",
                    "required": ["title", "synopsis", "releaseDate", "duration", "posterUrl", "addedDate"],
                    "properties": {
                        "title": {"type": "string", "example": "Interstellar"},
                        "synopsis": {"type": "string", "example": "Un voyage au-delà de notre système solaire."},
                        "releaseDate": {"type": "string", "format": "date", "example": "2014-11-05"},
                        "duration": {"type": "integer", "example": 169},
                        "posterUrl": {"type": "string", "example": "https://example.com/interstellar.jpg"},
                        "addedDate": {"type": "string", "format": "date", "example": "2026-11-20"},
                        "director": {"$ref": "#/definitions/DirectorReference"},
                        "classification": {"$ref": "#/definitions/ClassificationReference"},
                        "nativeLanguage": {"$ref": "#/definitions/LanguageReference"},
                        "languages": {"type": "array", "items": {"$ref": "#/definitions/LanguageReference"}},
                        "genre": {"type": "array", "items": {"$ref": "#/definitions/GenreReference"}},
                        "actors": {"type": "array", "items": {"$ref": "#/definitions/ActorReference"}},
                    },
                },
            },
        })
    database = MongoClient(MONGO_URI)[DATABASE_NAME]

    # DAOs
    directorDAO = DirectorDAO(database)
    actorDAO = ActorDAO(database)
    genreDAO = GenreDAO(database)
    languageDAO = LanguageDAO(database)
    classificationDAO = ClassificationDAO(database)
    filmDAO = FilmDAO(database)
    supportDAO = SupportDAO(database)
    supportTypeDAO = SupportTypeDAO(database)

    # Services
    directorService = DirectorService(directorDAO)
    actorService = ActorService(actorDAO)
    genreService = GenreService(genreDAO)
    languageService = LanguageService(languageDAO)
    classificationService = ClassificationService(classificationDAO)
    supportService = SupportService(supportDAO, filmDAO, supportTypeDAO)
    supportTypeService = SupportTypeService(supportTypeDAO, supportDAO)
    filmService = FilmService(
        filmDAO, directorDAO, genreDAO, languageDAO, classificationDAO, supportDAO
    )

    # Controllers
    app.register_blueprint(createDirectorBlueprint(directorService))
    app.register_blueprint(createActorBlueprint(actorService))
    app.register_blueprint(createGenreBlueprint(genreService))
    app.register_blueprint(createLanguageBlueprint(languageService))
    app.register_blueprint(createClassificationBlueprint(classificationService))
    app.register_blueprint(createFilmBlueprint(filmService))
    app.register_blueprint(createSupportBlueprint(supportService))
    app.register_blueprint(createSupportTypeBlueprint(supportTypeService))

    registerErrorHandlers(app)
    return app


if __name__ == "__main__":
    createApp().run(host="0.0.0.0", port=5000, debug=True)