@echo off
setlocal enabledelayedexpansion

echo ========================================
echo CONFIGURATION SAUVEGARDE AUTOMATIQUE POSTGRESQL
echo ========================================

echo Ce script va configurer une tache planifiee Windows pour sauvegarder
echo automatiquement votre volume PostgreSQL.

echo.
echo ========================================
echo OPTIONS DE PLANIFICATION
echo ========================================

echo 1. Sauvegarde quotidienne (recommande)
echo 2. Sauvegarde hebdomadaire
echo 3. Sauvegarde manuelle uniquement
echo 4. Supprimer la tache planifiee existante

set /p schedule_choice=Choisissez une option (1-4): 

if "%schedule_choice%"=="1" goto daily_backup
if "%schedule_choice%"=="2" goto weekly_backup
if "%schedule_choice%"=="3" goto manual_only
if "%schedule_choice%"=="4" goto remove_task
goto invalid_choice

:daily_backup
set TASK_NAME="PostgreSQL_Backup_Daily"
set SCHEDULE=/SC DAILY /TN %TASK_NAME%
set /p backup_time=Entrez l'heure de sauvegarde (format HH:MM, ex: 02:00): 
set SCHEDULE=%SCHEDULE% /ST %backup_time%
goto create_task

:weekly_backup
set TASK_NAME="PostgreSQL_Backup_Weekly"
set SCHEDULE=/SC WEEKLY /TN %TASK_NAME%
set /p backup_day=Entrez le jour de la semaine (MON,TUE,WED,THU,FRI,SAT,SUN): 
set /p backup_time=Entrez l'heure de sauvegarde (format HH:MM, ex: 02:00): 
set SCHEDULE=%SCHEDULE% /D %backup_day% /ST %backup_time%
goto create_task

:manual_only
echo.
echo Aucune tache planifiee ne sera creee.
echo Vous pouvez executer backup-postgres-volume.cmd manuellement.
goto end

:remove_task
echo.
echo Suppression des taches planifiees existantes...
schtasks /Delete /TN "PostgreSQL_Backup_Daily" /F 2>nul
schtasks /Delete /TN "PostgreSQL_Backup_Weekly" /F 2>nul
echo Taches supprimees.
goto end

:create_task
echo.
echo ========================================
echo CREATION DE LA TACHE PLANIFIEE
echo ========================================

set SCRIPT_PATH=%cd%\backup-postgres-volume.cmd
set LOG_PATH=%cd%\backups\postgres\scheduled_backup.log

echo Tache: %TASK_NAME%
echo Script: %SCRIPT_PATH%
echo Planification: %SCHEDULE%

echo.
echo Creation de la tache planifiee...
schtasks /Create %SCHEDULE% /TR "\"%SCRIPT_PATH%\" >> \"%LOG_PATH%\" 2>&1" /RU SYSTEM /F

if %ERRORLEVEL% EQU 0 (
    echo ✓ Tache planifiee creee avec succes!
    echo.
    echo La sauvegarde sera executee automatiquement selon la planification.
    echo Les logs seront sauvegardes dans: %LOG_PATH%
) else (
    echo ✗ Erreur lors de la creation de la tache planifiee
    echo Verifiez que vous executez ce script en tant qu'administrateur
)

goto end

:invalid_choice
echo Choix invalide. Veuillez choisir une option valide.
pause
goto :eof

:end
echo.
echo ========================================
echo VERIFICATION DES TACHES PLANIFIEES
echo ========================================

echo Taches PostgreSQL existantes:
schtasks /Query /TN "*PostgreSQL*" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Aucune tache PostgreSQL trouvee
)

echo.
echo Configuration terminee!
pause 