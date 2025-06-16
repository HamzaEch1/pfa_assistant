@echo off
echo 🔧 DIAGNOSTIC ET CORRECTION ERREURS CHATBOT
echo.

echo 📋 1. Vérification de l'état des conteneurs...
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 📋 2. Vérification des logs API (dernières 30 lignes)...
docker logs api --tail 30

echo.
echo 📋 3. Test de connectivité API...
echo Tentative de connexion à l'API...
curl -s http://localhost:8000/health || echo "❌ API inaccessible"

echo.
echo 📋 4. Vérification des services dépendants...
echo - PostgreSQL:
docker exec postgres_db pg_isready -U user -d mydb 2>nul && echo "✅ PostgreSQL OK" || echo "❌ PostgreSQL KO"

echo - Qdrant:
curl -s http://localhost:6333/healthz >nul && echo "✅ Qdrant OK" || echo "❌ Qdrant KO"

echo - Vault:
curl -s http://localhost:8200/v1/sys/health >nul && echo "✅ Vault OK" || echo "❌ Vault KO"

echo.
echo 🔧 5. Solutions automatiques...

echo Redémarrage de l'API...
docker-compose restart api

echo.
echo ⏳ Attente de 30 secondes pour redémarrage...
timeout /t 30

echo.
echo 📋 6. Nouveau test après redémarrage...
docker logs api --tail 10

echo.
echo 🎯 SOLUTIONS MANUELLES si le problème persiste:
echo.
echo A. Erreur 401 (Unauthorized):
echo    1. Videz le cache du navigateur (Ctrl+Shift+Suppr)
echo    2. Fermez et rouvrez le navigateur
echo    3. Reconnectez-vous à l'application
echo.
echo B. Timeout (requête trop lente):
echo    1. Vérifiez votre modèle OLLAMA: docker exec ollama ollama list
echo    2. Redémarrez OLLAMA: docker-compose restart ollama
echo    3. Attendez que le modèle se charge complètement
echo.
echo C. Erreur de conversations:
echo    1. Supprimez les cookies du site
echo    2. Reconnectez-vous
echo    3. Créez une nouvelle conversation
echo.
echo ✅ TESTS À EFFECTUER:
echo 1. Ouvrez http://localhost (ou votre URL)
echo 2. Connectez-vous avec vos identifiants
echo 3. Essayez de poser une question simple
echo 4. Vérifiez que la réponse arrive sans erreur 401
echo.
pause 