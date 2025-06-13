@echo off
echo 🔧 CONFIGURATION MODÈLE OLLAMA LÉGER
echo.

echo 📥 Téléchargement du modèle llama3.2:1b (plus rapide)...
ollama pull llama3.2:1b

echo.
echo 🧪 Test du modèle...
ollama run llama3.2:1b "Bonjour, réponds en français s'il te plaît"

echo.
echo ⚙️ Pour utiliser ce modèle par défaut dans votre API:
echo.
echo 1. Créez un fichier .env dans votre projet
echo 2. Ajoutez cette ligne: OLLAMA_MODEL_NAME=llama3.2:1b
echo 3. Ou modifiez votre configuration existante
echo.
echo 📝 Configuration actuelle dans docker-compose.yml:
echo    OLLAMA_MODEL_NAME: ${OLLAMA_MODEL_NAME:-llama3:8b}
echo.
echo 💡 Avec .env, cela deviendra: llama3.2:1b
echo.
echo ✅ AVANTAGES du modèle llama3.2:1b:
echo - Plus rapide (réponse en 2-10 secondes au lieu de 30-240s)
echo - Moins de RAM nécessaire (2GB au lieu de 8GB)
echo - Parfait pour un chatbot rapide
echo.
pause 