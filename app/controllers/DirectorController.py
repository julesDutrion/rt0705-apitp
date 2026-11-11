from flask import Blueprint, jsonify, request

from ..models.DirectorDTO import DirectorDTO
from ..services.DirectorService import DirectorService


def createDirectorBlueprint(directorService: DirectorService) -> Blueprint:
    blueprint = Blueprint("directors", __name__, url_prefix="/directors")

    @blueprint.get("")
    def getDirectors():
        name = request.args.get("name")
        directors = (
            directorService.searchDirectorsByName(name)
            if name
            else directorService.getAllDirectors()
        )
        return jsonify([director.toDict() for director in directors]), 200

    @blueprint.get("/<int:idDirector>")
    def getDirector(idDirector: int):
        director = directorService.getDirectorById(idDirector)
        return jsonify(director.toDict()), 200

    @blueprint.post("")
    def createDirector():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Invalid JSON body"}), 400
        try:
            director = DirectorDTO.fromDict(data)
        except (KeyError, TypeError) as e:
            return jsonify({"error": f"Invalid or missing field: {e}"}), 400
        directorService.createDirector(director)
        return jsonify(director.toDict()), 201

    return blueprint