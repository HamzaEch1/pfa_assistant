@echo off
setlocal enabledelayedexpansion

echo ========================================
echo GESTIONNAIRE DE SAUVEGARDE POSTGRESQL
echo ========================================

echo Bienvenue dans le gestionnaire centralisé de sauvegarde PostgreSQL
echo pour votre projet rag-almost.

echo.
echo ========================================
echo MENU PRINCIPAL
echo ========================================

echo 1. Créer une sauvegarde manuelle
echo 2. Restaurer une sauvegarde
echo 3. Vérifier l'intégrité des sauvegardes
echo 4. Configurer la sauvegarde automatique
echo 5. Nettoyer les anciennes sauvegardes
echo 6. Voir le statut des sauvegardes
echo 7. Aide et documentation
echo 8. Quitter

set /p choice=Choisissez une option (1-8): 

if "%choice%"=="1" goto manual_backup
if "%choice%"=="2" goto restore_backup
if "%choice%"=="3" goto verify_backups
if "%choice%"=="4" goto setup_schedule
if "%choice%"=="5" goto cleanup_backups
if "%choice%"=="6" goto backup_status
if "%choice%"=="7" goto help_docs
if "%choice%"=="8" goto end
goto invalid_choice

:manual_backup
echo.
echo ========================================
echo SAUVEGARDE MANUELLE
echo ========================================

if not exist "backup-postgres-volume.cmd" (
    echo ERREUR: Script backup-postgres-volume.cmd non trouvé!
    echo Assurez-vous que tous les scripts sont dans le même répertoire.
    pause
    goto :eof
)

echo Lancement de la sauvegarde manuelle...
call backup-postgres-volume.cmd
goto :eof

:restore_backup
echo.
echo ========================================
echo RESTAURATION DE SAUVEGARDE
echo ========================================

if not exist "restore-postgres-volume.cmd" (
    echo ERREUR: Script restore-postgres-volume.cmd non trouvé!
    pause
    goto :eof
)

echo Lancement de l'outil de restauration...
call restore-postgres-volume.cmd
goto :eof

:verify_backups
echo.
echo ========================================
echo VERIFICATION DES SAUVEGARDES
echo ========================================

if not exist "verify-postgres-backups.cmd" (
    echo ERREUR: Script verify-postgres-backups.cmd non trouvé!
    pause
    goto :eof
)

echo Lancement de la vérification...
call verify-postgres-backups.cmd
goto :eof

:setup_schedule
echo.
echo ========================================
echo CONFIGURATION SAUVEGARDE AUTOMATIQUE
echo ========================================

if not exist "setup-postgres-backup-schedule.cmd" (
    echo ERREUR: Script setup-postgres-backup-schedule.cmd non trouvé!
    pause
    goto :eof
)

echo Lancement de la configuration...
call setup-postgres-backup-schedule.cmd
goto :eof

:cleanup_backups
echo.
echo ========================================
echo NETTOYAGE DES SAUVEGARDES
echo ========================================

if not exist "cleanup-old-backups.cmd" (
    echo ERREUR: Script cleanup-old-backups.cmd non trouvé!
    pause
    goto :eof
)

echo Lancement du nettoyage...
call cleanup-old-backups.cmd
goto :eof

:backup_status
echo.
echo ========================================
echo STATUT DES SAUVEGARDES
echo ========================================

echo CONTENEURS POSTGRESQL:
docker-compose ps db
echo.

echo VOLUMES POSTGRESQL:
docker volume ls | findstr postgres
echo.

echo TACHES PLANIFIEES:
schtasks /Query /TN "*PostgreSQL*" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Aucune tâche planifiée PostgreSQL trouvée
)
echo.

echo SAUVEGARDES DISPONIBLES:
if exist "./backups/postgres" (
    echo Fichiers de sauvegarde:
    dir /b "./backups/postgres" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Aucun fichier de sauvegarde
    )
) else (
    echo Répertoire de sauvegarde n'existe pas encore
)
echo.

echo ESPACE DISQUE DOCKER:
docker system df

echo.
pause
goto :eof

:help_docs
echo.
echo ========================================
echo AIDE ET DOCUMENTATION
echo ========================================

echo STRUCTURE DES SAUVEGARDES:
echo.
echo Le système crée 3 types de sauvegardes:
echo 1. VOLUMES CLONES: Copies exactes du volume PostgreSQL
echo    - Format: ragalmost-main_postgres_data_backup_YYYYMMDD_HHMMSS
echo    - Avantage: Restauration très rapide
echo    - Inconvénient: Prend de l'espace disque
echo.
echo 2. ARCHIVES TAR.GZ: Fichiers compressés du volume
echo    - Format: postgres_backup_YYYYMMDD_HHMMSS.tar.gz
echo    - Avantage: Économise l'espace disque
echo    - Inconvénient: Restauration plus lente
echo.
echo 3. DUMPS SQL: Exportation SQL complète
echo    - Format: postgres_dump_YYYYMMDD_HHMMSS.sql
echo    - Avantage: Portable entre versions PostgreSQL
echo    - Inconvénient: Plus lent pour grandes bases
echo.

echo COMMANDES RAPIDES:
echo.
echo Sauvegarde rapide:
echo   backup-postgres-volume.cmd
echo.
echo Restauration d'urgence:
echo   restore-postgres-volume.cmd
echo.
echo Vérification intégrité:
echo   verify-postgres-backups.cmd
echo.

echo LOCALISATION DES SAUVEGARDES:
echo - Volumes: Dans Docker (docker volume ls)
echo - Fichiers: ./backups/postgres/
echo - Logs: ./backups/postgres/scheduled_backup.log
echo.

echo BONNES PRATIQUES:
echo - Effectuez une sauvegarde avant chaque mise à jour
echo - Testez régulièrement vos restaurations
echo - Gardez au moins 7 jours de sauvegardes
echo - Surveillez l'espace disque disponible
echo - Configurez une sauvegarde automatique quotidienne
echo.

pause
goto :eof

:invalid_choice
echo Choix invalide. Veuillez choisir une option valide.
pause
goto :eof

:end
echo.
echo ========================================
echo GESTIONNAIRE DE SAUVEGARDE FERMÉ
echo ========================================

echo Merci d'avoir utilisé le gestionnaire de sauvegarde PostgreSQL!
echo.
echo Rappel: Vos données sont précieuses, sauvegardez régulièrement!

pause 