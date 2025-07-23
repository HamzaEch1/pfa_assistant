@echo off
echo ========================================
echo CLONAGE URGENT VOLUME POSTGRESQL
echo ========================================

set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%

set ORIGINAL_VOLUME=ragalmost-main_postgres_data
set BACKUP_VOLUME=%ORIGINAL_VOLUME%_URGENT_%TIMESTAMP%

echo Volume original: %ORIGINAL_VOLUME%
echo Volume clone: %BACKUP_VOLUME%
echo Timestamp: %TIMESTAMP%

echo.
echo TEST DE DOCKER...
docker version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Docker n'est pas encore pret
    echo   Attendez encore 1-2 minutes et relancez ce script
    echo.
    echo Pour relancer: .\clone-postgres-urgent.cmd
    pause
    exit /b 1
)

echo ✓ Docker fonctionne!

echo.
echo VERIFICATION DU VOLUME ORIGINAL...
docker volume ls | findstr %ORIGINAL_VOLUME% >nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Volume %ORIGINAL_VOLUME% non trouve!
    echo.
    echo Volumes disponibles:
    docker volume ls
    pause
    exit /b 1
)

echo ✓ Volume %ORIGINAL_VOLUME% trouve!

echo.
echo CREATION DU VOLUME DE SAUVEGARDE...
docker volume create %BACKUP_VOLUME%

echo.
echo CLONAGE EN COURS...
echo Ceci peut prendre 1-2 minutes selon la taille de votre base...

docker run --rm -v %ORIGINAL_VOLUME%:/source -v %BACKUP_VOLUME%:/backup alpine sh -c "cp -a /source/. /backup/"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ ✓ ✓ CLONAGE REUSSI! ✓ ✓ ✓
    echo.
    echo Volume clone cree: %BACKUP_VOLUME%
    echo.
    echo VERIFICATION:
    docker volume ls | findstr postgres
    echo.
    echo VOS DONNEES SONT MAINTENANT CLONEES ET SECURISEES!
) else (
    echo.
    echo ✗ Erreur lors du clonage
    echo Verifiez que le volume original existe
)

echo.
echo ========================================
echo CLONAGE TERMINE
echo ========================================

pause 