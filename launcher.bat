@echo off
echo ==========================================
echo      APPLICATION PFE - CHATBOT VOCAL
echo ==========================================
echo.
echo Votre application est accessible sur :
echo.
echo 🌐 Application principale : http://127.0.0.1
echo 🌐 Frontend direct        : http://127.0.0.1:3000
echo 🌐 API Backend           : http://127.0.0.1:8000
echo.
echo ==========================================
echo.
echo Choix disponibles :
echo [1] Ouvrir l'application dans le navigateur
echo [2] Vérifier l'état des services
echo [3] Voir les logs
echo [Q] Quitter
echo.
set /p choice="Votre choix : "

if "%choice%"=="1" (
    echo Ouverture de l'application...
    start http://127.0.0.1
    goto menu
)
if "%choice%"=="2" (
    echo État des services Docker :
    docker ps --format "table {{.Names}}\t{{.Status}}"
    echo.
    pause
    goto menu
)
if "%choice%"=="3" (
    echo Logs récents de l'application :
    docker logs nginx_server --tail 10
    echo.
    pause
    goto menu
)
if /i "%choice%"=="Q" (
    exit
)

:menu
cls
goto :start
