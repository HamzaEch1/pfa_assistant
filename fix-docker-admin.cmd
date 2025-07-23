@echo off

:: Verification des droits administrateur
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Droits administrateur detectes - Demarrage de la reparation...
    goto :admin_repair
) else (
    echo Demande de droits administrateur...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:admin_repair
echo ========================================
echo REPARATION DOCKER/WSL EN MODE ADMIN
echo ========================================

echo ETAPE 1: Arret force de tous les processus Docker/WSL
taskkill /f /im "Docker Desktop.exe" 2>nul
taskkill /f /im "wslservice.exe" 2>nul
taskkill /f /im "wsl.exe" 2>nul

echo.
echo ETAPE 2: Arret force du service WSL
net stop LxssManager /y 2>nul
timeout /t 3 /nobreak >nul

echo.
echo ETAPE 3: Redemarrage du service WSL
net start LxssManager
timeout /t 5 /nobreak >nul

echo.
echo ETAPE 4: Test WSL
wsl --list --verbose

echo.
echo ETAPE 5: Demarrage Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo.
echo ETAPE 6: Attente du demarrage (45 secondes)
timeout /t 45 /nobreak

echo.
echo ETAPE 7: Test Docker
docker version
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ SUCCESS! Docker fonctionne!
    echo.
    echo VERIFICATION DE VOS VOLUMES:
    docker volume ls
    echo.
    echo VOS VOLUMES SONT SAUFS!
) else (
    echo.
    echo Docker demarre encore... Attendez 1-2 minutes et retestez:
    echo docker volume ls
)

echo.
echo ========================================
echo REPARATION TERMINEE
echo ========================================

echo Si Docker ne fonctionne toujours pas:
echo 1. Attendez 2-3 minutes
echo 2. Ouvrez Docker Desktop manuellement
echo 3. Testez: docker volume ls

pause 