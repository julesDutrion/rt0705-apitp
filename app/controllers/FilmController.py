from typing import List, Optional

from flask import Blueprint, g, jsonify, request
from werkzeug.datastructures import MultiDict

from ..models import FilmDTO
from ..services import FilmService
from ..decorators import optionalAuth, requireRole
from ..models import UserRole

def _findFilms(
    filmService: FilmService, args: MultiDict, idUser: Optional[int] = None
) -> List[FilmDTO]:
    filters = {
        "title": args.get("title"),
        "genre": args.get("genre", type=int),
        "director": args.get("director", type=int),
        "actor": args.get("actor", type=int),
        "language": args.get("language", type=int),
        "supportType": args.get("supportType", type=int),
    }

    return filmService.searchFilms(filters, idUser)


def createFilmBlueprint(filmService: FilmService) -> Blueprint:
    blueprint = Blueprint("films", __name__, url_prefix="/films")

    @blueprint.get("")
    @optionalAuth
    def getFilms():
        """
        Rechercher les films selon un ou plusieurs critères.
        ---
        tags:
          - Films
        security:
          - Bearer: []
          - {}
        parameters:
          - name: title
            in: query
            type: string
            required: false
            description: Titre ou partie du titre recherché.
          - name: genre
            in: query
            type: integer
            required: false
            description: Identifiant du genre.
          - name: director
            in: query
            type: integer
            required: false
            description: Identifiant du réalisateur.
          - name: actor
            in: query
            type: integer
            required: false
            description: Identifiant de l'acteur.
          - name: language
            in: query
            type: integer
            required: false
            description: Identifiant de la langue.
          - name: supportType
            in: query
            type: integer
            required: false
            description: Identifiant du type de support (idSupportType).
        responses:
          200:
            description: Liste des films correspondant aux critères.
            schema:
              type: array
              items:
                $ref: '#/definitions/Film'
          401:
            description: Jeton fourni invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Les informations du compte authentifié sont invalides.
            schema:
              $ref: '#/definitions/Error'
        """
        currentUser = g.currentUser
        idUser = currentUser.idUser if currentUser is not None else None
        films = _findFilms(filmService, request.args, idUser)
        return jsonify([film.toDict() for film in films]), 200

    @blueprint.get("/<string:idFilm>")
    @optionalAuth
    def getFilm(idFilm: str):
        """
        Récupérer un film par son identifiant.
        ---
        tags:
          - Films
        security:
          - Bearer: []
          - {}
        parameters:
          - name: idFilm
            in: path
            type: string
            required: true
            description: Identifiant du film.
        responses:
          200:
            description: Film trouvé.
            schema:
              $ref: '#/definitions/Film'
          404:
            description: Film introuvable ou non accessible.
            schema:
              $ref: '#/definitions/Error'
          401:
            description: Jeton fourni invalide ou expiré.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Les informations du compte authentifié sont invalides.
            schema:
              $ref: '#/definitions/Error'
        """
        currentUser = g.currentUser
        idUser = currentUser.idUser if currentUser is not None else None
        film = filmService.getFilmById(idFilm, idUser)
        return jsonify(film.toDict()), 200

    @blueprint.post("")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def createFilm():
        """
        Ajouter un film.
        ---
        tags:
          - Films
        consumes:
          - application/json
        parameters:
          - in: body
            name: film
            required: true
            schema:
              $ref: '#/definitions/FilmInput'
        responses:
          201:
            description: Film créé.
            schema:
              $ref: '#/definitions/Film'
          400:
            description: Corps JSON absent, invalide ou incomplet.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Un film avec cet identifiant existe déjà.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Une référence (réalisateur, classification, langue ou genre) est invalide.
            schema:
              $ref: '#/definitions/Error'
        """
        film = filmService.createFilm(request.get_json(silent=True))
        return jsonify(film.toDict()), 201

    @blueprint.put("/<string:idFilm>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def updateFilm(idFilm: str):
        """
        Modifier un film existant.
        ---
        tags:
          - Films
        consumes:
          - application/json
        parameters:
          - name: idFilm
            in: path
            type: string
            required: true
            description: Identifiant du film à modifier.
          - in: body
            name: film
            required: true
            schema:
              $ref: '#/definitions/FilmInput'
        responses:
          200:
            description: Film modifié.
            schema:
              $ref: '#/definitions/Film'
          400:
            description: Corps JSON invalide ou identifiant URL/corps différent.
            schema:
              $ref: '#/definitions/Error'
          404:
            description: Film à modifier introuvable.
            schema:
              $ref: '#/definitions/Error'
          422:
            description: Une référence (réalisateur, classification, langue ou genre) est invalide.
            schema:
              $ref: '#/definitions/Error'
        """
        updatedFilm = filmService.updateFilm(
            idFilm, request.get_json(silent=True)
        )
        return jsonify(updatedFilm.toDict()), 200

    @blueprint.delete("/<string:idFilm>")
    @requireRole(UserRole.ADMIN,UserRole.MANAGER)
    def deleteFilm(idFilm: str):
      
        """
        Supprimer un film.
        ---
        tags:
          - Films
        parameters:
          - name: idFilm
            in: path
            type: string
            required: true
            description: Identifiant du film à supprimer.
        responses:
          204:
            description: Film supprimé. Aucun contenu n'est renvoyé.
          404:
            description: Film introuvable.
            schema:
              $ref: '#/definitions/Error'
          409:
            description: Le film possède encore des supports associés.
            schema:
              $ref: '#/definitions/Error'
        """
        filmService.deleteFilm(idFilm)
        return "", 204

    return blueprint