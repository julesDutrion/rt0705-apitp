from typing import Any, Callable, Dict, TypeVar

from ..Exceptions import InvalidRequestError

DTO = TypeVar("DTO")


def dtoFromInput(
    data: Any,
    fromDictWithoutId: Callable[[Dict[str, Any]], DTO],
) -> DTO:
    """
    Méthode qui convertit des données de requête en DTO sans identifiant.

    :param data: Données reçues dans la requête.
    :param fromDictWithoutId: Convertisseur des données en DTO.
    :return: DTO construit à partir des données.
    :raises InvalidRequestError: Si les données sont absentes ou malformées.
    """
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return fromDictWithoutId(data)
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidRequestError(f"Invalid or missing field: {error}") from error
