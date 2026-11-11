"""Racine de composition : assemble les dépendances et crée l'application Flask."""

from flask import Flask
from pymongo import MongoClient

from config import DATABASE_NAME, MONGO_URI

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

from ErrorHandlers import registerErrorHandlers

def createApp() -> Flask:
    app = Flask(__name__)
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
    createApp().run(debug=True)