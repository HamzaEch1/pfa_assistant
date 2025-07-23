@echo off
setlocal enabledelayedexpansion

echo ========================================
echo NETTOYAGE DES ANCIENNES SAUVEGARDES POSTGRESQL
echo ========================================

set BACKUP_DIR=./backups/postgres
set DEFAULT_KEEP_DAYS=7
set DEFAULT_KEEP_VOLUMES=5

echo Repertoire de sauvegarde: %BACKUP_DIR%

echo.
echo ========================================
echo CONFIGURATION DU NETTOYAGE
echo ========================================

set /p keep_days=Garder les fichiers de moins de combien de jours? (defaut: %DEFAULT_KEEP_DAYS%): 
if "%keep_days%"=="" set keep_days=%DEFAULT_KEEP_DAYS%

set /p keep_volumes=Garder combien de volumes clones? (defaut: %DEFAULT_KEEP_VOLUMES%): 
if "%keep_volumes%"=="" set keep_volumes=%DEFAULT_KEEP_VOLUMES%

echo.
echo Configuration:
echo - Garder les fichiers de moins de %keep_days% jours
echo - Garder les %keep_volumes% volumes clones les plus recents

echo.
echo ========================================
echo ANALYSE DES SAUVEGARDES
echo ========================================

if not exist "%BACKUP_DIR%" (
    echo Le repertoire %BACKUP_DIR% n'existe pas.
    echo Aucun nettoyage necessaire.
    goto end
)

echo Fichiers actuels dans %BACKUP_DIR%:
dir /b "%BACKUP_DIR%" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Repertoire vide.
)

echo.
echo Volumes PostgreSQL actuels:
docker volume ls | findstr ragalmost-main_postgres_data

echo.
echo ========================================
echo NETTOYAGE DES FICHIERS ANCIENS
echo ========================================

echo Suppression des fichiers de plus de %keep_days% jours...

rem Supprimer les fichiers tar.gz anciens
forfiles /P "%BACKUP_DIR%" /M "*.tar.gz" /D -%keep_days% /C "cmd /c echo Suppression: @path && del @path" 2>nul

rem Supprimer les fichiers SQL anciens
forfiles /P "%BACKUP_DIR%" /M "*.sql" /D -%keep_days% /C "cmd /c echo Suppression: @path && del @path" 2>nul

echo.
echo ========================================
echo NETTOYAGE DES VOLUMES CLONES
echo ========================================

echo Recherche des volumes clones...

rem Lister tous les volumes de backup et les trier par date (approximative)
set /a counter=0
for /f "tokens=2" %%i in ('docker volume ls ^| findstr ragalmost-main_postgres_data_backup ^| sort /r') do (
    set /a counter+=1
    if !counter! GTR %keep_volumes% (
        echo Suppression du volume: %%i
        docker volume rm %%i 2>nul
        if !ERRORLEVEL! EQU 0 (
            echo ✓ Volume %%i supprime
        ) else (
            echo ✗ Erreur lors de la suppression de %%i
        )
    ) else (
        echo ✓ Volume conserve: %%i
    )
)

echo.
echo ========================================
echo VERIFICATION DE L'ESPACE DISQUE
echo ========================================

echo Espace utilise par Docker:
docker system df

echo.
echo Volumes Docker:
docker volume ls | findstr postgres

echo.
echo ========================================
echo OPTIMISATION DOCKER
echo ========================================

set /p cleanup_docker=Voulez-vous nettoyer les ressources Docker inutilisees? (oui/non): 

if "%cleanup_docker%"=="oui" (
    echo Nettoyage des ressources Docker inutilisees...
    docker system prune -f
    docker volume prune -f
    echo ✓ Nettoyage Docker termine
)

echo.
echo ========================================
echo RESUME DU NETTOYAGE
echo ========================================

echo Fichiers conserves:
if exist "%BACKUP_DIR%" (
    dir /b "%BACKUP_DIR%" 2>nul
    if %ERRORLEVEL% NEQ 0 echo Aucun fichier
) else (
    echo Repertoire n'existe pas
)

echo.
echo Volumes PostgreSQL conserves:
docker volume ls | findstr ragalmost-main_postgres_data

:end
echo.
echo ========================================
echo NETTOYAGE TERMINE
echo ========================================

echo Recommandation: Executez ce script regulierement pour maintenir
echo un espace disque optimal.

pause 