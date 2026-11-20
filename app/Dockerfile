
FROM python:3.12-slim

# Répertoire de travail à la racine
WORKDIR /

# Installation des dépendances
COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copie du package Python
COPY . /app

# Port exposé par l'API
EXPOSE 5000

# Démarrage de l'application comme module du package app
CMD ["python", "-m", "app.app"]
