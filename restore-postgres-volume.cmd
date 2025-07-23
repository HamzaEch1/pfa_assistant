@echo off
setlocal enabledelayedexpansion

echo ========================================
echo SCRIPT DE RESTAURATION VOLUME POSTGRESQL
echo ========================================

set ORIGINAL_VOLUME=ragalmost-main_postgres_data
set BACKUP_DIR=./backups/postgres

echo Volume cible: %ORIGINAL_VOLUME%
echo Repertoire de sauvegarde: %BACKUP_DIR%

echo.
echo ========================================
echo CHOIX DU TYPE DE RESTAURATION
echo ========================================

echo 1. Restaurer depuis un volume clone
echo 2. Restaurer depuis un fichier tar.gz
echo 3. Restaurer depuis un dump SQL
echo 4. Lister les sauvegardes disponibles
echo 5. Quitter

set /p choice=Choisissez une option (1-5): 

if "%choice%"=="1" goto restore_volume
if "%choice%"=="2" goto restore_tar
if "%choice%"=="3" goto restore_sql
if "%choice%"=="4" goto list_backups
if "%choice%"=="5" goto end
goto invalid_choice

:restore_volume
echo.
echo ========================================
echo RESTAURATION DEPUIS VOLUME CLONE
echo ========================================

echo Volumes PostgreSQL disponibles:
docker volume ls | findstr postgres

echo.
set /p backup_volume=Entrez le nom du volume de sauvegarde: 

echo Verification du volume de sauvegarde...
docker volume ls | findstr %backup_volume% >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Le volume %backup_volume% n'existe pas!
    pause
    goto end
)

echo.
echo ATTENTION: Cette operation va ecraser toutes les donnees actuelles!
set /p confirm=Confirmer la restauration? (oui/non): 

if not "%confirm%"=="oui" (
    echo Restauration annulee.
    goto end
)

echo Arret des conteneurs...
docker-compose stop db

echo Creation/recreation du volume cible...
docker volume rm %ORIGINAL_VOLUME% 2>nul
docker volume create %ORIGINAL_VOLUME%

echo Restauration des donnees...
docker run --rm -v %backup_volume%:/source -v %ORIGINAL_VOLUME%:/target alpine sh -c "cp -a /source/. /target/"

if %ERRORLEVEL% EQU 0 (
    echo ✓ Restauration reussie!
    echo Redemarrage des conteneurs...
    docker-compose up -d db
) else (
    echo ✗ Erreur lors de la restauration
)

goto end

:restore_tar
echo.
echo ========================================
echo RESTAURATION DEPUIS FICHIER TAR.GZ
echo ========================================

if not exist "%BACKUP_DIR%" (
    echo ERREUR: Le repertoire %BACKUP_DIR% n'existe pas!
    pause
    goto end
)

echo Fichiers tar.gz disponibles:
dir /b "%BACKUP_DIR%\*.tar.gz" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Aucun fichier tar.gz trouve dans %BACKUP_DIR%
    pause
    goto end
)

echo.
set /p backup_file=Entrez le nom du fichier tar.gz (sans le chemin): 

if not exist "%BACKUP_DIR%\%backup_file%" (
    echo ERREUR: Le fichier %BACKUP_DIR%\%backup_file% n'existe pas!
    pause
    goto end
)

echo.
echo ATTENTION: Cette operation va ecraser toutes les donnees actuelles!
set /p confirm=Confirmer la restauration? (oui/non): 

if not "%confirm%"=="oui" (
    echo Restauration annulee.
    goto end
)

echo Arret des conteneurs...
docker-compose stop db

echo Creation/recreation du volume cible...
docker volume rm %ORIGINAL_VOLUME% 2>nul
docker volume create %ORIGINAL_VOLUME%

echo Restauration des donnees...
docker run --rm -v %cd%/%BACKUP_DIR%:/backup -v %ORIGINAL_VOLUME%:/target alpine sh -c "cd /target && tar -xzf /backup/%backup_file%"

if %ERRORLEVEL% EQU 0 (
    echo ✓ Restauration reussie!
    echo Redemarrage des conteneurs...
    docker-compose up -d db
) else (
    echo ✗ Erreur lors de la restauration
)

goto end

:restore_sql
echo.
echo ========================================
echo RESTAURATION DEPUIS DUMP SQL
echo ========================================

if not exist "%BACKUP_DIR%" (
    echo ERREUR: Le repertoire %BACKUP_DIR% n'existe pas!
    pause
    goto end
)

echo Fichiers SQL disponibles:
dir /b "%BACKUP_DIR%\*.sql" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Aucun fichier SQL trouve dans %BACKUP_DIR%
    pause
    goto end
)

echo.
set /p sql_file=Entrez le nom du fichier SQL (sans le chemin): 

if not exist "%BACKUP_DIR%\%sql_file%" (
    echo ERREUR: Le fichier %BACKUP_DIR%\%sql_file% n'existe pas!
    pause
    goto end
)

echo.
echo ATTENTION: Cette operation va ecraser toutes les donnees actuelles!
set /p confirm=Confirmer la restauration? (oui/non): 

if not "%confirm%"=="oui" (
    echo Restauration annulee.
    goto end
)

echo Verification que PostgreSQL est en cours d'execution...
docker-compose ps db | findstr Up >nul
if %ERRORLEVEL% NEQ 0 (
    echo Demarrage de PostgreSQL...
    docker-compose up -d db
    timeout /t 10 /nobreak >nul
)

echo Restauration de la base de donnees...
docker-compose exec -T db psql -U user -d postgres < "%BACKUP_DIR%\%sql_file%"

if %ERRORLEVEL% EQU 0 (
    echo ✓ Restauration SQL reussie!
) else (
    echo ✗ Erreur lors de la restauration SQL
)

goto end

:list_backups
echo.
echo ========================================
echo SAUVEGARDES DISPONIBLES
echo ========================================

echo VOLUMES CLONES:
docker volume ls | findstr ragalmost-main_postgres_data_backup

echo.
echo FICHIERS TAR.GZ:
if exist "%BACKUP_DIR%" (
    dir /b "%BACKUP_DIR%\*.tar.gz" 2>nul
    if %ERRORLEVEL% NEQ 0 echo Aucun fichier tar.gz trouve
) else (
    echo Repertoire %BACKUP_DIR% n'existe pas
)

echo.
echo FICHIERS SQL:
if exist "%BACKUP_DIR%" (
    dir /b "%BACKUP_DIR%\*.sql" 2>nul
    if %ERRORLEVEL% NEQ 0 echo Aucun fichier SQL trouve
) else (
    echo Repertoire %BACKUP_DIR% n'existe pas
)

echo.
pause
goto :eof

:invalid_choice
echo Choix invalide. Veuillez choisir une option valide.
pause
goto :eof

:end
echo.
echo Script termine.
pause 