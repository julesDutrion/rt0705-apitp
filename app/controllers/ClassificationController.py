from flask import Blueprint, jsonify, request

from ..models.ClassificationDTO import ClassificationDTO
from ..services.ClassificationServcie import ClassificationService


def createClassificationBlueprint(
    classificationService: ClassificationService,
) -> Blueprint:
    blueprint = Blueprint("classifications", __name__, url_prefix="/classifications")

    @blueprint.get("")
    def getClassifications():
        minAge = request.args.get("minAge", type=int)
        classifications = (
            classificationService.getClassificationsByMinAge(minAge)
            if minAge is not None
            else classificationService.getAllClassifications()
        )
        return jsonify([c.toDict() for c in classifications]), 200

    @blueprint.get("/<int:idClassification>")
    def getClassification(idClassification: int):
        classification = classificationService.getClassificationById(idClassification)
        return jsonify(classification.toDict()), 200

    @blueprint.post("")
    def createClassification():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Invalid JSON body"}), 400
        try:
            classification = ClassificationDTO.fromDict(data)
        except (KeyError, TypeError) as e:
            return jsonify({"error": f"Invalid or missing field: {e}"}), 400
        classificationService.createClassification(classification)
        return jsonify(classification.toDict()), 201

    return blueprint