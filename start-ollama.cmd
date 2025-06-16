@echo off
echo 🚀 DÉMARRAGE OLLAMA LOCAL
echo.

echo 📋 Vérification si OLLAMA est déjà en cours...
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ OLLAMA déjà en cours d'exécution
    echo Processus OLLAMA actifs:
    tasklist /FI "IMAGENAME eq ollama.exe"
) else (
    echo ⚠️ OLLAMA non démarré, lancement...
    echo.
    echo 🚀 Démarrage d'OLLAMA en arrière-plan...
    start "OLLAMA Server" ollama serve
    
    echo ⏳ Attente de 15 secondes pour initialisation...
    timeout /t 15
    
    echo 📋 Vérification après démarrage...
    tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
    if %ERRORLEVEL% EQU 0 (
        echo ✅ OLLAMA démarré avec succès !
    ) else (
        echo ❌ Échec du démarrage d'OLLAMA
        echo.
        echo 💡 Solutions:
        echo 1. Vérifiez qu'OLLAMA est installé
        echo 2. Exécutez manuellement: ollama serve
        echo 3. Téléchargez OLLAMA: https://ollama.com/download/windows
        pause
        exit /b 1
    )
)

echo.
echo 🧪 Test de connectivité...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ OLLAMA API accessible sur port 11434
) else (
    echo ❌ OLLAMA API inaccessible
    echo Attente supplémentaire de 10 secondes...
    timeout /t 10
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo ✅ OLLAMA API maintenant accessible
    ) else (
        echo ❌ Problème de connectivité persistant
    )
)

echo.
echo 📝 OLLAMA est maintenant prêt !
echo.
echo 🎯 Prochaines étapes:
echo 1. Gardez cette fenêtre ouverte (OLLAMA fonctionne)
echo 2. Testez votre chatbot: http://localhost
echo 3. Le timeout devrait disparaître
echo.
echo ⚠️ IMPORTANT: Ne fermez pas cette fenêtre si vous voulez garder OLLAMA actif
echo.
pause 