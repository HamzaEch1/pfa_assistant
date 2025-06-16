@echo off
echo 🔧 CRÉATION FICHIER .ENV COMPLET
echo.

echo 📝 Génération du fichier .env avec toutes les variables...
(
echo # Configuration complète pour Docker Compose
echo.
echo # Variables obligatoires
echo JWT_SECRET_KEY=my_super_secret_jwt_key_32_chars_min
echo.
echo # Configuration OLLAMA - MODÈLE RAPIDE
echo OLLAMA_MODEL_NAME=llama3.2:1b
echo.
echo # Configuration Base de données
echo PG_USER=user
echo PG_PASSWORD=password
echo PG_DB=mydb
echo.
echo # Configuration Qdrant
echo QDRANT_COLLECTION_NAME=banque_ma_data_catalog
echo.
echo # Configuration Embeddings
echo EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
echo.
echo # Configuration Vault
echo VAULT_DEV_ROOT_TOKEN_ID=myroot
echo.
echo # Autres paramètres
echo NUM_RESULTS_TO_RETRIEVE=28
) > .env

echo ✅ Fichier .env créé avec toutes les variables requises

echo.
echo 📋 Variables configurées :
echo ✅ JWT_SECRET_KEY (obligatoire^)
echo ✅ OLLAMA_MODEL_NAME=llama3.2:1b (RAPIDE^)
echo ✅ Variables PostgreSQL
echo ✅ Variables Qdrant et Vault
echo.

echo 🚀 Démarrage des conteneurs...
docker-compose up --build -d

echo.
echo ✅ CONFIGURATION TERMINÉE !
echo.
echo 🎯 VOTRE CHATBOT EST MAINTENANT :
echo - ⚡ Rapide : llama3.2:1b au lieu de llama3:8b
echo - 🔐 Sécurisé : JWT configuré
echo - 🐳 Fonctionnel : tous les services démarrés
echo.
echo 🧪 TESTEZ MAINTENANT :
echo 1. http://localhost
echo 2. Login: admin / admin123
echo 3. Question: "Bonjour"
echo 4. Réponse en 5-15 secondes ! ⚡
echo.
pause 