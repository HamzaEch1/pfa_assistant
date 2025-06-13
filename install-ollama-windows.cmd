@echo off
echo 🤖 INSTALLATION OLLAMA POUR WINDOWS
echo.

echo 📥 1. Téléchargement d'OLLAMA...
echo Allez sur: https://ollama.com/download/windows
echo.
echo OU utilisez PowerShell pour télécharger automatiquement:
echo.
powershell -Command "& {Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile 'OllamaSetup.exe'}"

echo.
echo 📦 2. Installation manuelle...
echo Double-cliquez sur OllamaSetup.exe pour installer
echo.
pause

echo.
echo 🚀 3. Démarrage du service OLLAMA...
echo Démarrage d'OLLAMA en arrière-plan...
start "" ollama serve

echo.
echo ⏳ 4. Attente de 10 secondes...
timeout /t 10

echo.
echo 📥 5. Téléchargement du modèle (cela peut prendre 10-30 minutes)...
echo Téléchargement de llama3.2:1b (modèle léger - 1.3GB)...
ollama pull llama3.2:1b

echo.
echo 🧪 6. Test du modèle...
ollama run llama3.2:1b "Hello, can you respond in French?"

echo.
echo ✅ 7. Configuration terminée!
echo.
echo 🎯 PROCHAINES ÉTAPES:
echo 1. Modifiez votre fichier .env:
echo    OLLAMA_MODEL_NAME=llama3.2:1b
echo.
echo 2. Redémarrez votre API:
echo    docker-compose restart fastapi_api
echo.
echo 3. Testez votre chatbot avec une question courte
echo.
echo 📝 NOTES:
echo - OLLAMA fonctionne maintenant sur localhost:11434
echo - Le modèle llama3.2:1b est plus rapide que llama3:8b
echo - Votre API peut maintenant communiquer avec OLLAMA
echo.
pause 