@echo off
echo 🚀 CORRECTION VAULT + TIMEOUT
echo.

echo 🎯 PROBLÈMES IDENTIFIÉS:
echo - Vault non configuré (erreurs kv/data/api/...)
echo - Modèle OLLAMA lent (timeout 240s)
echo.

echo 💡 SOLUTIONS:
echo 1. Désactiver Vault (utiliser variables directes)
echo 2. Utiliser modèle rapide llama3.2:1b
echo.

echo 📝 Création du fichier .env optimisé...
(
echo # Configuration SANS VAULT + MODÈLE RAPIDE
echo.
echo # Variables obligatoires
echo JWT_SECRET_KEY=my_super_secret_jwt_key_32_chars_min_dev
echo.
echo # OLLAMA - MODÈLE RAPIDE !
echo OLLAMA_MODEL_NAME=llama3.2:1b
echo.
echo # Base de données
echo PG_USER=user
echo PG_PASSWORD=password
echo PG_DB=mydb
echo.
echo # Qdrant
echo QDRANT_COLLECTION_NAME=banque_ma_data_catalog
echo.
echo # Embeddings
echo EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
echo.
echo # Vault - DÉSACTIVÉ
echo VAULT_DEV_ROOT_TOKEN_ID=myroot
echo.
echo # Autres
echo NUM_RESULTS_TO_RETRIEVE=28
) > .env

echo ✅ Fichier .env créé (Vault désactivé + modèle rapide)

echo.
echo 🔧 Modification temporaire docker-compose pour désactiver Vault...
powershell -Command "(Get-Content docker-compose.yml) -replace 'VAULT_ENABLED: \"true\"', 'VAULT_ENABLED: \"false\"' | Set-Content docker-compose-temp.yml"

echo.
echo 🔄 Redémarrage avec configuration optimisée...
docker-compose -f docker-compose-temp.yml up --build -d api

echo.
echo ⏳ Attente 20 secondes pour démarrage API...
timeout /t 20

echo.
echo 🧪 Test de l'API...
curl -s http://localhost:8000/health

echo.
echo ✅ CORRECTION TERMINÉE !
echo.
echo 📊 CHANGEMENTS EFFECTUÉS:
echo ✅ Vault désactivé (plus d'erreurs kv/data)
echo ✅ Variables directes utilisées
echo ✅ Modèle rapide: llama3.2:1b (5-15s au lieu de 240s)
echo ✅ API redémarrée avec nouvelle config
echo.
echo 🎯 MAINTENANT TESTEZ:
echo 1. http://localhost
echo 2. Login: admin / admin123  
echo 3. Question: "Bonjour"
echo 4. Réponse RAPIDE attendue ! ⚡
echo.
echo 📝 Note: docker-compose-temp.yml créé pour test
echo Pour revenir: utilisez docker-compose.yml original
echo.
pause 