@echo off
echo 💾 Sauvegarde de la configuration monitoring complète...

set "BACKUP_DIR=monitoring-backup-%date:~10,4%-%date:~4,2%-%date:~7,2%"
echo.
echo 📁 Création du dossier de sauvegarde: %BACKUP_DIR%
mkdir "%BACKUP_DIR%" 2>nul

echo.
echo 📋 Copie des fichiers de configuration...

REM Fichiers principaux
copy "docker-compose.yml" "%BACKUP_DIR%\" >nul
copy "Dockerfile.metricbeat" "%BACKUP_DIR%\" >nul
copy "SETUP-MONITORING.md" "%BACKUP_DIR%\" >nul

REM Scripts de maintenance
copy "restart-metricbeat.cmd" "%BACKUP_DIR%\" >nul
copy "diagnose-metricbeat.ps1" "%BACKUP_DIR%\" >nul
copy "fix-docker-module.ps1" "%BACKUP_DIR%\" >nul
copy "save-monitoring-config.cmd" "%BACKUP_DIR%\" >nul

REM Dossier metricbeat
mkdir "%BACKUP_DIR%\metricbeat" 2>nul
copy "metricbeat\metricbeat.yml" "%BACKUP_DIR%\metricbeat\" >nul

REM Dossier elasticsearch  
mkdir "%BACKUP_DIR%\elasticsearch" 2>nul
copy "elasticsearch\init-dataviews.sh" "%BACKUP_DIR%\elasticsearch\" >nul

echo.
echo 📄 Création du fichier README...
(
echo # 📊 Configuration Monitoring Docker - Sauvegarde
echo.
echo ## 🚀 Installation rapide sur nouvelle machine
echo.
echo 1. Copiez tous ces fichiers dans un nouveau dossier
echo 2. Ouvrez un terminal dans ce dossier  
echo 3. Lancez: docker-compose up -d
echo 4. Attendez 2-3 minutes
echo 5. Allez dans Kibana: http://localhost:5601
echo 6. Créez le dataview 'metricbeat-*'
echo.
echo ## 📁 Fichiers inclus:
echo.
echo - docker-compose.yml          : Configuration principale
echo - Dockerfile.metricbeat       : Image Metricbeat personnalisée  
echo - metricbeat/metricbeat.yml   : Config Metricbeat optimisée
echo - elasticsearch/init-dataviews.sh : Script init Kibana
echo - restart-metricbeat.cmd      : Script redémarrage
echo - diagnose-metricbeat.ps1     : Script diagnostic
echo - fix-docker-module.ps1       : Script correction
echo - SETUP-MONITORING.md         : Guide complet
echo.
echo ## 🔧 En cas de problème:
echo.
echo 1. Windows: double-cliquez sur restart-metricbeat.cmd
echo 2. Linux/Mac: docker-compose restart metricbeat
echo 3. Rafraîchissez le dataview dans Kibana ^(bouton 🔄^)
echo.
echo ## ✅ Résultat attendu:
echo.
echo Visualisation des métriques Docker et système:
echo - docker.container.name
echo - docker.cpu.total.pct  
echo - docker.memory.usage.pct
echo - system.cpu.total.pct
echo - system.memory.used.pct
echo.
echo Date de sauvegarde: %date% %time%
) > "%BACKUP_DIR%\README.md"

echo.
echo ✅ Sauvegarde terminée!
echo.
echo 📁 Dossier créé: %BACKUP_DIR%
echo 📋 Fichiers sauvegardés:
dir /b "%BACKUP_DIR%"
echo.
echo 🎯 Instructions pour nouvelle machine:
echo    1. Copiez le dossier %BACKUP_DIR% sur la nouvelle machine
echo    2. cd %BACKUP_DIR%
echo    3. docker-compose up -d
echo    4. Attendez 2-3 minutes et allez dans Kibana
echo.
pause 