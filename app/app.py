"""Racine de composition : assemble les dépendances et crée l'application Flask."""

import os

from flask import Flask
from flasgger import Swagger
from pymongo import MongoClient

from .config.database import database as DATABASE_NAME
from .config.database import uri as MONGO_URI

from .controllers.ClassificationController import createClassificationBlueprint
from .controllers.DirectorController import createDirectorBlueprint
from .controllers.FilmController import createFilmBlueprint
from .controllers.GenreController import createGenreBlueprint
from .controllers.LanguageController import createLanguageBlueprint

'''Listes des daos'''
from .dao.ClassificationDAO import ClassificationDAO
from .dao.DirectorDAO import DirectorDAO
from .dao.FilmsDAO import FilmDAO
from .dao.GenreDAO import GenreDAO
from .dao.LanguageDAO import LanguageDAO

'''Listes des services'''
from .services.LanguageService import LanguageService
from .services.FilmService import FilmService
from .services.GenreService import GenreService
from .services.ClassificationServcie import ClassificationService
from .services.DirectorService import DirectorService

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
                "Director": {
                    "type": "object",
                    "required": ["idDirector", "lastName", "firstName"],
                    "properties": {
                        "idDirector": {"type": "integer", "example": 1},
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
                "Language": {
                    "type": "object",
                    "required": ["idLanguage", "code", "name"],
                    "properties": {
                        "idLanguage": {"type": "integer", "example": 1},
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
                "Support": {
                    "type": "object",
                    "required": ["idSupport", "storageLocation", "filePath", "fileSize", "fileFormat"],
                    "properties": {
                        "idSupport": {"type": "integer", "example": 1},
                        "storageLocation": {"type": "string", "example": "local"},
                        "filePath": {"type": "string", "example": "/films/interstellar.mp4"},
                        "fileSize": {"type": "integer", "example": 1500000000},
                        "fileFormat": {"type": "string", "example": "mp4"},
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
                        "support": {"$ref": "#/definitions/Support"},
                        "nativeLanguage": {"$ref": "#/definitions/Language"},
                        "languages": {"type": "array", "items": {"$ref": "#/definitions/Language"}},
                        "genre": {"type": "array", "items": {"$ref": "#/definitions/Genre"}},
                        "actors": {"type": "array", "items": {"$ref": "#/definitions/Actor"}},
                    },
                },
            },
        })
    database = MongoClient(MONGO_URI)[DATABASE_NAME]

    # DAOs
    directorDAO = DirectorDAO(database)
    genreDAO = GenreDAO(database)
    languageDAO = LanguageDAO(database)
    classificationDAO = ClassificationDAO(database)
    filmDAO = FilmDAO(database)

    # Services
    directorService = DirectorService(directorDAO)
    genreService = GenreService(genreDAO)
    languageService = LanguageService(languageDAO)
    classificationService = ClassificationService(classificationDAO)
    filmService = FilmService(
        filmDAO, directorDAO, genreDAO, languageDAO, classificationDAO
    )

    # Controllers
    app.register_blueprint(createDirectorBlueprint(directorService))
    app.register_blueprint(createGenreBlueprint(genreService))
    app.register_blueprint(createLanguageBlueprint(languageService))
    app.register_blueprint(createClassificationBlueprint(classificationService))
    app.register_blueprint(createFilmBlueprint(filmService))

    registerErrorHandlers(app)
    return app


if __name__ == "__main__":
    createApp().run(host="0.0.0.0", port=5000, debug=True)