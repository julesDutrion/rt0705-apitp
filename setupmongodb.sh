
#!/bin/bash

set -Eeuo pipefail

# ==========================================
# Configuration
# ==========================================

NETWORK_NAME="videotheque-network"
CONTAINER_NAME="mongodb"
VOLUME_NAME="mongodb-data"
IMAGE_NAME="mongo:8"
DATABASE_NAME="videotheque"

# Accès local uniquement pour MongoDB Compass via SSH
MONGO_BIND_ADDRESS="127.0.0.1"
MONGO_HOST_PORT="27017"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# ==========================================
# Fonctions
# ==========================================

read_env_value() {
    local key="$1"
    sed -n "s/^${key}=//p" "$ENV_FILE" | head -n 1 | tr -d '\r'
}

write_env_file() {
    umask 077

    cat > "$ENV_FILE" <<EOF
MONGO_USERNAME=$MONGO_USER
MONGO_PASSWORD=$MONGO_PASSWORD
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DATABASE=$DATABASE_NAME
MONGO_AUTH_SOURCE=admin
JWT_SECRET_KEY=clef_secrete_generee
EOF

    chmod 600 "$ENV_FILE"
}

# ==========================================
# Vérification de Docker
# ==========================================

echo "Vérification de Docker..."

if ! command -v docker >/dev/null 2>&1; then
    echo "Erreur : Docker n'est pas installé."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Erreur : Docker n'est pas accessible."
    exit 1
fi

# ==========================================
# Création du réseau
# ==========================================

echo "Vérification du réseau Docker..."

if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    docker network create "$NETWORK_NAME"
    echo "Réseau créé."
else
    echo "Réseau existant."
fi

# ==========================================
# Vérification du volume
# ==========================================

echo "Vérification du volume MongoDB..."

VOLUME_EXISTS=false

if docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
    VOLUME_EXISTS=true
    echo "Volume existant : les données seront conservées."
else
    docker volume create "$VOLUME_NAME"
    echo "Nouveau volume créé."
fi

# ==========================================
# Gestion des identifiants
# ==========================================

if [[ "$VOLUME_EXISTS" == true ]]; then

    echo "Récupération des identifiants existants..."

    if [[ ! -f "$ENV_FILE" ]]; then
        echo "Erreur : aucun fichier .env disponible."
        exit 1
    fi

    MONGO_USER="$(read_env_value MONGO_USERNAME)"
    MONGO_PASSWORD="$(read_env_value MONGO_PASSWORD)"
    MONGO_AUTH_SOURCE="$(read_env_value MONGO_AUTH_SOURCE)"
    MONGO_AUTH_SOURCE="${MONGO_AUTH_SOURCE:-admin}"

else

    echo "Nouvelle installation MongoDB."

    read -r -p "Nom d'utilisateur MongoDB : " MONGO_USER
    read -r -s -p "Mot de passe MongoDB : " MONGO_PASSWORD
    echo

    if [[ -z "$MONGO_USER" || -z "$MONGO_PASSWORD" ]]; then
        echo "Erreur : identifiants vides."
        exit 1
    fi

    if [[ ! "$MONGO_USER" =~ ^[a-zA-Z0-9._-]+$ ]] ||
       [[ ! "$MONGO_PASSWORD" =~ ^[a-zA-Z0-9._-]+$ ]]; then
        echo "Erreur : utilisez uniquement lettres, chiffres, points,"
        echo "tirets et underscores dans les identifiants."
        exit 1
    fi

    MONGO_AUTH_SOURCE="admin"
    write_env_file

fi

if [[ -z "$MONGO_USER" || -z "$MONGO_PASSWORD" ]]; then
    echo "Erreur : identifiants MongoDB manquants."
    exit 1
fi

if [[ "$MONGO_AUTH_SOURCE" != "admin" ]]; then
    echo "Erreur : MONGO_AUTH_SOURCE doit être admin."
    exit 1
fi

# ==========================================
# Gestion de l'ancien conteneur
# ==========================================

if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then

    echo "Un conteneur MongoDB existe déjà."

    read -r -p "Souhaites-tu le recréer ? (o/N) : " RESPONSE

    if [[ "$RESPONSE" != "o" && "$RESPONSE" != "O" ]]; then
        echo "Opération annulée."
        exit 0
    fi

    docker rm -f "$CONTAINER_NAME"

fi

# ==========================================
# Vérification du port local
# ==========================================

echo "Vérification du port $MONGO_HOST_PORT..."

if ss -ltn | grep -q ":${MONGO_HOST_PORT} "; then
    echo "Erreur : le port $MONGO_HOST_PORT est déjà utilisé."
    echo "Libérez ce port avant de lancer MongoDB."
    exit 1
fi

# ==========================================
# Démarrage de MongoDB
# ==========================================

echo "Démarrage de MongoDB..."

if [[ "$VOLUME_EXISTS" == true ]]; then

    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        -p "$MONGO_BIND_ADDRESS:$MONGO_HOST_PORT:27017" \ # A supprimé
        -v "$VOLUME_NAME:/data/db" \
        "$IMAGE_NAME"

else

    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        -p "$MONGO_BIND_ADDRESS:$MONGO_HOST_PORT:27017" \
        -v "$VOLUME_NAME:/data/db" \
        -e MONGO_INITDB_ROOT_USERNAME="$MONGO_USER" \
        -e MONGO_INITDB_ROOT_PASSWORD="$MONGO_PASSWORD" \
        "$IMAGE_NAME"

fi

# ==========================================
# Attente de MongoDB
# ==========================================

echo "Attente du démarrage de MongoDB..."

MONGO_READY=false

for i in {1..30}; do

    if docker exec "$CONTAINER_NAME" mongosh --quiet \
        --username "$MONGO_USER" \
        --password "$MONGO_PASSWORD" \
        --authenticationDatabase admin \
        --eval 'db.adminCommand({ ping: 1 }).ok' \
        2>/dev/null | grep -q 1; then

        MONGO_READY=true
        echo "MongoDB est prêt et l'authentification fonctionne."
        break

    fi

    sleep 2

done

if [[ "$MONGO_READY" == false ]]; then
    echo "Erreur : MongoDB n'est pas prêt ou l'authentification a échoué."
    docker logs "$CONTAINER_NAME" --tail 50
    exit 1
fi

# ==========================================
# Création de la base et de la collection
# ==========================================

echo "Initialisation de la base de données..."

docker exec "$CONTAINER_NAME" mongosh \
    --quiet \
    --username "$MONGO_USER" \
    --password "$MONGO_PASSWORD" \
    --authenticationDatabase admin \
    --eval "
        const database = db.getSiblingDB('$DATABASE_NAME');

        if (!database.getCollectionNames().includes('films')) {
            database.createCollection('films');
            print('Collection films créée.');
        } else {
            print('Collection films déjà existante.');
        }
    "

# ==========================================
# Fin
# ==========================================

echo
echo "=========================================="
echo "Installation MongoDB terminée !"
echo "=========================================="
echo "Conteneur : $CONTAINER_NAME"
echo "Réseau    : $NETWORK_NAME"
echo "Volume    : $VOLUME_NAME"
echo "Base      : $DATABASE_NAME"
echo "Collection: films"
echo "Port local: $MONGO_BIND_ADDRESS:$MONGO_HOST_PORT"
echo "=========================================="
