# API de vidéothèque

API REST développée avec Flask et MongoDB pour gérer un catalogue de films, ses
supports physiques ou numériques, les utilisateurs et les emprunts.

## Fonctionnalités

- Gestion des films, réalisateurs, acteurs, genres, langues et classifications.
- Gestion des types de supports et des exemplaires associés aux films.
- Création de comptes avec confirmation du mot de passe et authentification JWT.
- Autorisations selon les rôles `consulteur`, `manager` et `adminstrateur`.
- Filtrage des films selon l'âge du compte lorsqu'un utilisateur authentifié
  consulte le catalogue.
- Emprunt de supports physiques, calcul de leur disponibilité et suivi des
  retours.
- Documentation interactive de l'API avec Swagger.

Les emprunts durent 30 jours. Leur statut (`IN_PROGRESS`, `OVERDUE` ou
`RETURNED`) est calculé à la lecture. Un support physique ne peut avoir qu'un
emprunt actif à la fois ; la contrainte est également garantie par un index
MongoDB. Aucun système de notifications n'est actuellement inclus.

## Technologies et architecture

- Python 3.12, Flask, PyMongo et MongoDB.
- JWT pour l'authentification ; bcrypt pour le stockage des mots de passe.
- Organisation en couches : `controllers` (HTTP), `services` (règles métier),
  `dao` (MongoDB), `models` (DTO), et `decorators` (contrôle d'accès).
- `app/app.py` assemble les composants et expose la fabrique `createApp()`.
  Elle peut recevoir une base de données en paramètre, notamment pour les tests.

## Configuration

L'application lit sa configuration dans un fichier `.env` à la racine du
projet. Pour une configuration manuelle :

```bash
cp .env.example .env
```

Renseignez ensuite les variables suivantes :

| Variable | Description |
| --- | --- |
| `MONGO_USERNAME` | Utilisateur MongoDB |
| `MONGO_PASSWORD` | Mot de passe MongoDB |
| `MONGO_HOST` | Hôte MongoDB ; utilisez `127.0.0.1` hors du réseau Docker |
| `MONGO_PORT` | Port MongoDB, généralement `27017` |
| `MONGO_DATABASE` | Base utilisée par l'API, généralement `videotheque` |
| `MONGO_AUTH_SOURCE` | Base d'authentification MongoDB, généralement `admin` |
| `JWT_SECRET_KEY` | Clé secrète utilisée pour signer les jetons JWT |

Ne publiez jamais le fichier `.env` ni la clé JWT. Le fichier `.env.example`
contient uniquement des valeurs indicatives.

## Lancer l'API en local

Après avoir installé et configuré MongoDB :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r app/requirements.txt
```

Configurez `.env` pour l'hôte MongoDB local, puis démarrez l'API depuis la
racine du dépôt :

```bash
.venv/bin/python -m app.app
```

L'API écoute sur le port `5000`. La documentation interactive Swagger est
disponible à l'adresse `http://localhost:5000/apidocs/`. Elle peut être
désactivée avec `SWAGGER_ENABLED=false`.

### Initialiser MongoDB avec Docker

Le script `setupmongodb.sh` prépare le réseau et le volume Docker, démarre
MongoDB, crée la collection initiale et peut proposer de créer le compte
administrateur. Il nécessite Docker ainsi qu'un environnement virtuel contenant
les dépendances de l'application :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r app/requirements.txt
./setupmongodb.sh
```

Le script demande les identifiants MongoDB lors d'une nouvelle installation et
génère le fichier `.env`. Le compte administrateur initial utilise le login
`admin` ; son adresse e-mail et son mot de passe sont demandés pendant le
bootstrap.

### Déployer l'API avec Docker

Après avoir initialisé MongoDB, lancez :

```bash
./deploy.sh
```

Ce script construit l'image `videotheque-api` depuis `app/Dockerfile`, puis
démarre le conteneur `flask-api` sur le port `5000`. Il requiert le fichier
`.env` et le réseau Docker `videotheque-network` créés par
`setupmongodb.sh`.

## Authentification et rôles

La connexion se fait sur `POST /auth/login`. Le jeton retourné doit être envoyé
dans l'en-tête :

```http
Authorization: Bearer <jeton>
```

Les jetons expirent après une heure. Les valeurs de rôle exposées par l'API
sont `consulteur` (utilisateur), `manager` et `adminstrateur` (administrateur).
Les routes de lecture du catalogue sont publiques, sauf les emprunts et les
routes utilisateurs protégées. Les opérations de modification du catalogue
sont réservées aux managers et aux administrateurs.

## Principales routes

Les identifiants entre accolades représentent des paramètres de chemin.

### Utilisateurs et authentification

| Méthode | Route | Accès |
| --- | --- | --- |
| `POST` | `/users` | Public — inscription |
| `POST` | `/auth/login` | Public — connexion |
| `GET` | `/users` | Administrateur |
| `GET` | `/users/{idUser}` | Utilisateur authentifié |
| `GET` | `/users/login/{login}` | Administrateur |
| `PUT` | `/users/{idUser}` | Compte personnel ; administrateur pour les autres comptes |
| `PUT` | `/users/{idUser}/role` | Administrateur, sauf modification de son propre rôle |
| `DELETE` | `/users/{idUser}` | Administrateur |

Les réponses publiques des utilisateurs ne contiennent jamais le hash du mot
de passe. La création d'un compte requiert `password` et `confirmPassword`.

### Catalogue et supports

Les routes suivantes proposent des opérations `GET` publiques et des
opérations `POST`, `PUT` et `DELETE` réservées aux managers et administrateurs :

- `/films`
- `/actors`
- `/directors`
- `/genres`
- `/languages`
- `/classifications`
- `/support-types`
- `/supports`

Les films peuvent être filtrés par titre, genre, réalisateur, acteur, langue ou
type de support. Les supports se consultent également par film avec
`GET /supports/film/{idFilm}`. La réponse indique `isAvailable` pour un support
physique ; cette valeur est `null` pour un support numérique.

Les lectures de films restent accessibles sans jeton. Lorsqu'un utilisateur
`consulteur` fournit un JWT valide, la liste et le détail sont filtrés selon
l'âge calculé à partir de sa date de naissance et de la classification du film.
Les managers et administrateurs ne sont pas soumis à ce filtre. Un JWT fourni
mais invalide entraîne une réponse `401`.

### Emprunts

| Méthode | Route | Accès |
| --- | --- | --- |
| `POST` | `/loans` | Utilisateur authentifié |
| `GET` | `/loans/me` | Utilisateur authentifié — ses emprunts |
| `GET` | `/loans/me/{idLoan}` | Utilisateur authentifié — détail de ses emprunts |
| `GET` | `/loans` | Manager ou administrateur |
| `GET` | `/loans/user/{login}` | Manager ou administrateur |
| `GET` | `/loans/{idLoan}` | Manager ou administrateur |
| `PATCH` | `/loans/{idLoan}/return` | Manager ou administrateur |

Le corps de `POST /loans` contient uniquement l'identifiant du support :

```json
{
  "idPhysicalSupport": 12
}
```

L'utilisateur est identifié à partir du JWT, jamais depuis le corps de la
requête. La date de début et la date de retour effective sont fixées par l'API ;
la date prévue est calculée à 30 jours. Le retour renseigne la date effective
et rend le support de nouveau disponible.

## Réponses d'erreur

Les erreurs métier sont renvoyées au format JSON avec un champ `error`.
L'API utilise notamment les codes `400` (requête invalide), `401`
(authentification), `403` (autorisation), `404` (ressource absente), `409`
(conflit) et `422` (référence invalide).

## Tests

Le script dédié crée `.venv` si nécessaire, installe les dépendances de
développement manquantes et exécute toute la suite :

```bash
./run_tests.sh
```

Les options pytest peuvent être ajoutées, par exemple :

```bash
./run_tests.sh -k loan
```

Les tests utilisent `mongomock` et ne nécessitent pas de serveur MongoDB réel.
La configuration pytest impose un seuil minimal de couverture de 80 %.
