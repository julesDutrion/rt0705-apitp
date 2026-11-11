from typing import Any
 
from flask import Blueprint, jsonify, request
 
from Exceptions import InvalidRequestError
from ..models.LanguageDTO import LanguageDTO
from ..services.LanguageService import LanguageService
 
 
def _toLanguageDTO(data: Any) -> LanguageDTO:
    if not isinstance(data, dict):
        raise InvalidRequestError("Invalid JSON body")
    try:
        return LanguageDTO.fromDict(data)
    except (KeyError, TypeError) as e:
        raise InvalidRequestError(f"Invalid or missing field: {e}")
 
 
def createLanguageBlueprint(languageService: LanguageService) -> Blueprint:
    blueprint = Blueprint("languages", __name__, url_prefix="/languages")
 
    @blueprint.get("")
    def getLanguages():
        languages = languageService.getAllLanguages()
        return jsonify([language.toDict() for language in languages]), 200
 
    @blueprint.get("/<int:idLanguage>")
    def getLanguage(idLanguage: int):
        language = languageService.getLanguageById(idLanguage)
        return jsonify(language.toDict()), 200
 
    @blueprint.get("/code/<string:code>")
    def getLanguageByCode(code: str):
        language = languageService.getLanguageByCode(code)
        return jsonify(language.toDict()), 200
 
    @blueprint.post("")
    def createLanguage():
        language = languageService.createLanguage(
            _toLanguageDTO(request.get_json(silent=True))
        )
        return jsonify(language.toDict()), 201
 
    return blueprint
