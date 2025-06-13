@echo off
echo 🔍 VÉRIFICATION STATUT OLLAMA
echo.

echo 📋 1. Test si OLLAMA est installé...
ollama --version 2>nul && echo "✅ OLLAMA installé" || echo "❌ OLLAMA non installé"

echo.
echo 📋 2. Test de connectivité OLLAMA...
curl -s http://localhost:11434/api/tags 2>nul && echo "✅ OLLAMA fonctionne" || echo "❌ OLLAMA ne répond pas"

echo.
echo 📋 3. Vérification des modèles disponibles...
ollama list 2>nul || echo "❌ Impossible de lister les modèles"

echo.
echo 📋 4. Test de l'API...
curl -s http://localhost:8000/health | findstr healthy && echo "✅ API accessible" || echo "❌ API problème"

echo.
echo 🎯 DIAGNOSTIC:
echo.

REM Vérifier si OLLAMA est installé
ollama --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ PROBLÈME: OLLAMA n'est pas installé
    echo.
    echo 💡 SOLUTION:
    echo    1. Lancez: install-ollama-windows.cmd
    echo    2. Ou allez sur: https://ollama.com/download/windows
    echo    3. Installez et configurez OLLAMA
    goto :end
)

REM Vérifier si OLLAMA fonctionne
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ PROBLÈME: OLLAMA installé mais ne fonctionne pas
    echo.
    echo 💡 SOLUTION:
    echo    1. Démarrez OLLAMA: ollama serve
    echo    2. Ou redémarrez le service OLLAMA
    echo    3. Vérifiez le port 11434
    goto :end
)

echo ✅ OLLAMA fonctionne correctement!
echo.
echo 🧪 Test avec un modèle simple...
ollama run llama3.2:1b "test" --timeout 10 && echo "✅ Modèle répond" || echo "⚠️ Modèle lent ou absent"

:end
echo.
echo 📝 PROCHAINES ÉTAPES si problème résolu:
echo    1. Redémarrez votre API: docker-compose restart fastapi_api
echo    2. Testez votre chatbot avec une question courte
echo    3. Le timeout devrait disparaître
echo.
pause 