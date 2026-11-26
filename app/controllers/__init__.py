from .AuthController import createAuthBlueprint
from .ClassificationController import createClassificationBlueprint
from .ActorController import createActorBlueprint
from .DirectorController import createDirectorBlueprint
from .FilmController import createFilmBlueprint
from .GenreController import createGenreBlueprint
from .LanguageController import createLanguageBlueprint
from .SupportController import createSupportBlueprint
from .SupportTypeController import createSupportTypeBlueprint
from .UserController import createUserBlueprint

__all__ = [
    "createActorBlueprint",
    "createAuthBlueprint",
    "createClassificationBlueprint",
    "createDirectorBlueprint",
    "createFilmBlueprint",
    "createGenreBlueprint",
    "createLanguageBlueprint",
    "createSupportBlueprint",
    "createSupportTypeBlueprint",
    "createUserBlueprint",
]
