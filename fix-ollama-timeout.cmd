@echo off
echo 🤖 CORRECTION TIMEOUT OLLAMA
echo.

echo 📋 1. Vérification du statut OLLAMA...
docker exec ollama ollama list

echo.
echo 📋 2. Vérification des logs OLLAMA...
docker logs ollama --tail 15

echo.
echo 🔧 3. Redémarrage d'OLLAMA...
docker-compose restart ollama

echo.
echo ⏳ 4. Attente du chargement du modèle (60 secondes)...
timeout /t 60

echo.
echo 🧪 5. Test du modèle...
echo Test simple du modèle OLLAMA...
docker exec ollama ollama run llama3:8b "Hello, are you working?" || echo "❌ Modèle non répondant"

echo.
echo 📋 6. Vérification des variables d'environnement API...
docker exec api env | findstr OLLAMA || echo "❌ Variables OLLAMA manquantes"

echo.
echo 🔧 7. Solutions spécifiques au timeout:

echo.
echo A. Si le modèle ne répond pas:
echo    - Le modèle est peut-être trop volumineux pour votre RAM
echo    - Essayez un modèle plus petit: ollama pull llama3.2:1b
echo.
echo B. Si l'API timeout (240s):
echo    - Le modèle met trop de temps à générer la réponse
echo    - Réduisez la longueur de vos questions
echo    - Vérifiez la charge CPU/RAM
echo.
echo C. Configuration recommandée:
echo    - RAM minimum: 8GB pour llama3:8b
echo    - RAM recommandée: 16GB
echo    - CPU: 4+ cores
echo.
echo ✅ PROCHAINES ÉTAPES:
echo 1. Attendez 2-3 minutes que OLLAMA se stabilise
echo 2. Testez avec une question courte (max 10 mots)
echo 3. Si toujours lent, changez de modèle:
echo    docker exec ollama ollama pull llama3.2:1b
echo    Puis modifiez OLLAMA_MODEL_NAME=llama3.2:1b dans .env
echo.
pause 