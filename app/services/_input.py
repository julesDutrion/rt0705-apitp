from typing import Any, Callable, Dict, TypeVar

from ..Exceptions import InvalidRequestError

DTO = TypeVar("DTO")


def dtoFromInput(
    data: Any,
    fromDictWithoutId: Callable[[Dict[str, Any]], DTO],
) -> DTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return fromDictWithoutId(data)
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidRequestError(f"Invalid or missing field: {error}") from error
