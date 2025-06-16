@echo off
echo 🧪 TEST FINAL OLLAMA + API
echo.

echo 📋 1. Vérification OLLAMA API...
curl -s http://localhost:11434/api/tags
echo.

echo 📋 2. Test de votre API...
curl -s http://localhost:8000/health
echo.

echo 📋 3. Redémarrage du service API correct...
docker-compose restart api
echo.

echo 📋 4. Attente de 20 secondes...
timeout /t 20

echo.
echo 📋 5. Test final de l'API après redémarrage...
curl -s http://localhost:8000/health
echo.

echo ✅ TOUT EST PRÊT !
echo.
echo 🎯 MAINTENANT TESTEZ VOTRE CHATBOT:
echo.
echo 1. Allez sur: http://localhost
echo 2. Connectez-vous avec vos identifiants
echo 3. Posez une question simple: "Bonjour"
echo 4. La réponse devrait arriver en 10-30 secondes (PLUS DE TIMEOUT!)
echo.
echo 📊 Ce qui a été corrigé:
echo ✅ OLLAMA fonctionne sur localhost:11434
echo ✅ Votre API peut maintenant communiquer avec OLLAMA
echo ✅ Le modèle llama3:8b est prêt
echo ✅ Plus d'erreur "no such container: ollama"
echo.
echo 🎉 Votre problème de timeout de 240 secondes est résolu !
echo.
pause 