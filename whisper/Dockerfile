# Dockerfile pour Whisper service léger
FROM python:3.10-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier seulement les fichiers nécessaires (pas le main.py original)
COPY requirements_light.txt ./requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Créer les dossiers nécessaires
RUN mkdir -p /tmp/whisper_audio /tmp/whisper_results

# Copier le code source léger en tant que main.py
COPY main_light.py ./main.py

# Exposer le port
EXPOSE 8004

# Variables d'environnement
ENV PYTHONPATH=/app

# Démarrer le service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
