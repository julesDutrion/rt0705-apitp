
FROM python:3.12-slim

# Répertoire de travail dans le conteneur
WORKDIR /app

# Installation des dépendances
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Port exposé par l'API
EXPOSE 5000

# Démarrage de l'application Flask
CMD ["python", "app.py"]
