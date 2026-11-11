
#!/bin/bash

CONTAINER_NAME="flask-api"
IMAGE_NAME="videotheque-api"
NETWORK_NAME="videotheque-network"

echo "Vérification du conteneur ${CONTAINER_NAME}..."

# Vérifie si le conteneur existe (actif ou arrêté)
if [ "$(docker ps -aq -f name=^${CONTAINER_NAME}$)" ]; then
    echo "Le conteneur existe déjà. Suppression..."
    docker rm -f "$CONTAINER_NAME"

    if [ $? -ne 0 ]; then
        echo "Erreur lors de la suppression du conteneur."
        exit 1
    fi
fi

echo "Construction de l'image Docker..."
docker build -t "$IMAGE_NAME" ./app

if [ $? -ne 0 ]; then
    echo "Erreur lors de la construction de l'image."
    exit 1
fi

echo "Création du nouveau conteneur..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -p 5000:5000 \
    "$IMAGE_NAME"

if [ $? -ne 0 ]; then
    echo "Erreur lors du démarrage du conteneur."
    exit 1
fi

echo "Déploiement terminé !"
