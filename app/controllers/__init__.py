from .ClassificationController import createClassificationBlueprint
from .ActorController import createActorBlueprint
from .DirectorController import createDirectorBlueprint
from .FilmController import createFilmBlueprint
from .GenreController import createGenreBlueprint
from .LanguageController import createLanguageBlueprint

__all__ = [
    "createActorBlueprint",
    "createClassificationBlueprint",
    "createDirectorBlueprint",
    "createFilmBlueprint",
    "createGenreBlueprint",
    "createLanguageBlueprint",
]
