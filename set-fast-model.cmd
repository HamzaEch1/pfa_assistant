@echo off
echo ⚡ CONFIGURATION MODÈLE RAPIDE
echo.

echo ⚙️ Création du fichier .env...
echo OLLAMA_MODEL_NAME=llama3.2:1b > .env
echo ✅ Fichier .env créé avec modèle rapide

echo.
echo 🔄 Redémarrage de l'API...
docker-compose restart api

echo.
echo ⏳ Attente de 15 secondes...
timeout /t 15

echo.
echo ✅ CONFIGURATION TERMINÉE !
echo.
echo 🎯 Changement effectué:
echo - Avant: llama3:8b (4.7GB, lent, timeout 240s)
echo - Maintenant: llama3.2:1b (1.3GB, rapide, 5-15s)
echo.
echo 🧪 TESTEZ MAINTENANT:
echo 1. http://localhost
echo 2. Login: admin / admin123
echo 3. Posez une question: "Bonjour"
echo 4. Réponse rapide attendue !
echo.
pause 