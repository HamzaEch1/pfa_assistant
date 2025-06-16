@echo off
echo 🚀 DÉMARRAGE OLLAMA avec votre modèle existant
echo.

echo 📋 Modèles détectés:
echo - llama3:latest (4.7 GB)
echo - llama3:8b (4.7 GB)
echo.

echo 🔄 Démarrage du serveur OLLAMA...
echo ⚠️  IMPORTANT: Gardez cette fenêtre ouverte !
echo.

echo Démarrage en cours...
start "OLLAMA Server" cmd /k "echo 🔴 SERVEUR OLLAMA ACTIF - NE FERMEZ PAS CETTE FENETRE && ollama serve"

echo ⏳ Attente de 10 secondes pour initialisation...
timeout /t 10

echo.
echo 🧪 Test de connectivité OLLAMA...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ OLLAMA API accessible !
) else (
    echo ⚠️ OLLAMA pas encore prêt, attente supplémentaire...
    timeout /t 10
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ OLLAMA API maintenant accessible !
    ) else (
        echo ❌ Problème de démarrage OLLAMA
    )
)

echo.
echo 🧪 Test rapide du modèle llama3:8b...
echo (Cela peut prendre 30-60 secondes la première fois)
ollama run llama3:8b "Bonjour, réponds brièvement" --timeout 60

echo.
echo 🔧 Redémarrage de votre API pour appliquer les changements...
docker-compose restart fastapi_api

echo.
echo ✅ CONFIGURATION TERMINÉE !
echo.
echo 🎯 Votre configuration:
echo - OLLAMA local avec llama3:8b (parfait pour votre API)
echo - API: host.docker.internal:11434 ✅
echo - Modèle: llama3:8b ✅
echo.
echo 📝 TESTS À EFFECTUER:
echo 1. Allez sur votre chatbot: http://localhost
echo 2. Connectez-vous
echo 3. Posez une question: "Bonjour"
echo 4. La réponse devrait arriver en 10-30 secondes (plus de timeout!)
echo.
echo ⚠️ RAPPEL: Ne fermez pas la fenêtre "OLLAMA Server" qui s'est ouverte
echo.
pause 