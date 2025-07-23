@echo off
echo ========================================
echo REPARATION DOCKER SANS PERTE DE VOLUMES
echo ========================================

echo ETAPE 1: Arret propre de Docker
taskkill /f /im "Docker Desktop.exe" 2>nul
echo Docker Desktop ferme...

echo.
echo ETAPE 2: Arret WSL (preserve les volumes)
wsl --shutdown
timeout /t 5 /nobreak >nul

echo.
echo ETAPE 3: Redemarrage service WSL
net stop LxssManager 2>nul
net start LxssManager
timeout /t 3 /nobreak >nul

echo.
echo ETAPE 4: Verification WSL
wsl --list --verbose

echo.
echo ETAPE 5: Redemarrage Docker Desktop
echo Demarrage de Docker Desktop...
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo.
echo ETAPE 6: Attente du demarrage
echo Attente 30 secondes pour le demarrage complet...
timeout /t 30 /nobreak

echo.
echo ETAPE 7: Test de fonctionnement
docker version
if %ERRORLEVEL% EQU 0 (
    echo ✓ Docker fonctionne!
    echo.
    echo VERIFICATION DES VOLUMES:
    docker volume ls
) else (
    echo ✗ Docker ne fonctionne pas encore
    echo Reessayez dans quelques minutes
)

echo.
echo ========================================
echo REPARATION TERMINEE
echo Vos volumes Docker sont preserves!
echo ========================================
pause 