@echo off
echo 🔧 Redémarrage de Metricbeat avec configuration Docker améliorée...

echo.
echo ⏹️ Arrêt de Metricbeat...
docker-compose stop metricbeat

echo.
echo 🔨 Reconstruction de l'image...
docker-compose build --no-cache metricbeat

echo.
echo 🚀 Redémarrage...
docker-compose up -d metricbeat

echo.
echo ⏳ Attente de 20 secondes...
timeout /t 20

echo.
echo 📋 Logs récents:
docker logs metricbeat --tail 10

echo.
echo ✅ Terminé! Vérifiez dans Kibana dans 2-3 minutes.
echo 📱 Instructions:
echo    1. Allez dans Kibana (http://localhost:5601)
echo    2. Management ^> Data Views
echo    3. Sélectionnez votre dataview et cliquez sur Refresh 🔄
echo    4. Allez dans Discover pour voir si docker.container.name apparaît
pause 