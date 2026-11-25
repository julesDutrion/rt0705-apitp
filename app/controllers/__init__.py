from .ClassificationController import createClassificationBlueprint
from .ActorController import createActorBlueprint
from .DirectorController import createDirectorBlueprint
from .FilmController import createFilmBlueprint
from .GenreController import createGenreBlueprint
from .LanguageController import createLanguageBlueprint
from .SupportController import createSupportBlueprint
from .SupportTypeController import createSupportTypeBlueprint

__all__ = [
    "createActorBlueprint",
    "createClassificationBlueprint",
    "createDirectorBlueprint",
    "createFilmBlueprint",
    "createGenreBlueprint",
    "createLanguageBlueprint",
    "createSupportBlueprint",
    "createSupportTypeBlueprint",
]
