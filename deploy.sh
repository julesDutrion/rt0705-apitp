
#!/bin/bash

CONTAINER_NAME="flask-api"
IMAGE_NAME="videotheque-api"
NETWORK_NAME="videotheque-network"

# Récupération du répertoire contenant ce script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ENV_FILE="$SCRIPT_DIR/.env"
APP_DIR="$SCRIPT_DIR/app"

echo "Vérification de la configuration..."

if [ ! -f "$ENV_FILE" ]; then
    echo "Erreur : fichier .env introuvable."
    exit 1
fi

echo "Construction de l'image Docker..."

if ! docker build -t "$IMAGE_NAME" "$APP_DIR"; then
    echo "Erreur lors de la construction de l'image."
    exit 1
fi

echo "Vérification de l'existence de l'ancien conteneur..."

# Vérifie si le conteneur existe (actif ou arrêté)
if [ "$(docker ps -aq -f name=^${CONTAINER_NAME}$)" ]; then
    echo "Le conteneur existe déjà. Suppression..."

    if ! docker rm -f "$CONTAINER_NAME"; then
        echo "Erreur lors de la suppression du conteneur."
        exit 1
    fi
fi

echo "Création du nouveau conteneur..."

if ! docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    --env-file "$ENV_FILE" \
    -p 5000:5000 \
    "$IMAGE_NAME"; then

    echo "Erreur lors du démarrage du conteneur."
    exit 1
fi

echo "Déploiement terminé !"

echo "Vérification du démarrage..."

sleep 2

if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" = "true" ]; then
    echo "L'API fonctionne !"
else
    echo "Attention : le conteneur s'est arrêté."
    echo "Consulte les logs avec : docker logs $CONTAINER_NAME"
    exit 1
fi
