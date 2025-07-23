@echo off
setlocal enabledelayedexpansion

echo ========================================
echo SCRIPT DE SAUVEGARDE VOLUME POSTGRESQL
echo ========================================

set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

set ORIGINAL_VOLUME=ragalmost-main_postgres_data
set BACKUP_VOLUME=%ORIGINAL_VOLUME%_backup_%TIMESTAMP%
set BACKUP_DIR=./backups/postgres
set BACKUP_FILE=%BACKUP_DIR%/postgres_backup_%TIMESTAMP%.tar

echo Timestamp: %TIMESTAMP%
echo Volume original: %ORIGINAL_VOLUME%
echo Volume de sauvegarde: %BACKUP_VOLUME%
echo Fichier de sauvegarde: %BACKUP_FILE%

echo.
echo ========================================
echo VERIFICATION DES VOLUMES EXISTANTS
echo ========================================

docker volume ls | findstr %ORIGINAL_VOLUME%
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Le volume %ORIGINAL_VOLUME% n'existe pas!
    echo Veuillez d'abord demarrer vos conteneurs PostgreSQL
    pause
    exit /b 1
)

echo.
echo ========================================
echo CREATION DU REPERTOIRE DE SAUVEGARDE
echo ========================================

if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo Repertoire %BACKUP_DIR% cree
) else (
    echo Repertoire %BACKUP_DIR% existe deja
)

echo.
echo ========================================
echo METHODE 1: CLONE DU VOLUME
echo ========================================

echo Clonage du volume %ORIGINAL_VOLUME% vers %BACKUP_VOLUME%...
docker volume create %BACKUP_VOLUME%
docker run --rm -v %ORIGINAL_VOLUME%:/source -v %BACKUP_VOLUME%:/backup alpine sh -c "cp -a /source/. /backup/"

if %ERRORLEVEL% EQU 0 (
    echo ✓ Volume clone avec succes: %BACKUP_VOLUME%
) else (
    echo ✗ Erreur lors du clonage du volume
)

echo.
echo ========================================
echo METHODE 2: EXPORT VERS FICHIER TAR
echo ========================================

echo Export du volume vers un fichier tar...
docker run --rm -v %ORIGINAL_VOLUME%:/source -v %cd%/%BACKUP_DIR%:/backup alpine tar -czf /backup/postgres_backup_%TIMESTAMP%.tar.gz -C /source .

if %ERRORLEVEL% EQU 0 (
    echo ✓ Export reussi: %BACKUP_FILE%.gz
) else (
    echo ✗ Erreur lors de l'export
)

echo.
echo ========================================
echo METHODE 3: DUMP SQL COMPLET
echo ========================================

echo Creation d'un dump SQL de la base de donnees...
docker-compose exec -T db pg_dumpall -U user > %BACKUP_DIR%/postgres_dump_%TIMESTAMP%.sql

if %ERRORLEVEL% EQU 0 (
    echo ✓ Dump SQL cree: %BACKUP_DIR%/postgres_dump_%TIMESTAMP%.sql
) else (
    echo ✗ Erreur lors du dump SQL (conteneur peut-etre arrete)
)

echo.
echo ========================================
echo RESUME DES SAUVEGARDES CREEES
echo ========================================

echo 1. Volume clone: %BACKUP_VOLUME%
echo 2. Archive tar.gz: %BACKUP_DIR%/postgres_backup_%TIMESTAMP%.tar.gz
echo 3. Dump SQL: %BACKUP_DIR%/postgres_dump_%TIMESTAMP%.sql

echo.
echo ========================================
echo VERIFICATION DES VOLUMES
echo ========================================

echo Volumes PostgreSQL disponibles:
docker volume ls | findstr postgres

echo.
echo ========================================
echo INFORMATIONS DE RESTAURATION
echo ========================================

echo Pour restaurer depuis le volume clone:
echo docker run --rm -v %BACKUP_VOLUME%:/source -v ragalmost-main_postgres_data:/target alpine sh -c "cp -a /source/. /target/"

echo.
echo Pour restaurer depuis le fichier tar.gz:
echo docker run --rm -v %cd%/%BACKUP_DIR%:/backup -v ragalmost-main_postgres_data:/target alpine sh -c "cd /target && tar -xzf /backup/postgres_backup_%TIMESTAMP%.tar.gz"

echo.
echo Pour restaurer depuis le dump SQL:
echo docker-compose exec -T db psql -U user -d mydb ^< %BACKUP_DIR%/postgres_dump_%TIMESTAMP%.sql

echo.
echo ========================================
echo SAUVEGARDE TERMINEE!
echo ========================================

pause 