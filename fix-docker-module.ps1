# Script pour corriger le module Docker de Metricbeat
Write-Host "🔧 CORRECTION MODULE DOCKER METRICBEAT" -ForegroundColor Green

# 1. Arrêter Metricbeat
Write-Host "`n⏹️  Arrêt de Metricbeat..." -ForegroundColor Yellow
try {
    docker-compose stop metricbeat
    Write-Host "✅ Metricbeat arrêté" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors de l'arrêt: $_" -ForegroundColor Red
}

# 2. Vérifier la configuration actuelle
Write-Host "`n🔍 Vérification de la configuration..." -ForegroundColor Yellow
if (Test-Path "metricbeat/metricbeat.yml") {
    Write-Host "✅ Configuration trouvée" -ForegroundColor Green
} else {
    Write-Host "❌ Configuration manquante" -ForegroundColor Red
    exit 1
}

# 3. Recréer le conteneur avec les bonnes permissions
Write-Host "`n🔨 Reconstruction du conteneur..." -ForegroundColor Yellow
try {
    docker-compose build --no-cache metricbeat
    Write-Host "✅ Image reconstruite" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors de la reconstruction: $_" -ForegroundColor Red
}

# 4. Redémarrer avec logging verbeux
Write-Host "`n🚀 Redémarrage avec logs verbeux..." -ForegroundColor Yellow
try {
    docker-compose up -d metricbeat
    Write-Host "✅ Metricbeat redémarré" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur lors du redémarrage: $_" -ForegroundColor Red
}

# 5. Attendre 30 secondes et vérifier les logs
Write-Host "`n⏳ Attente de 30 secondes pour initialisation..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "`n📋 Logs récents:" -ForegroundColor Yellow
try {
    $logs = docker logs metricbeat --tail 15 2>&1
    Write-Host $logs -ForegroundColor White
} catch {
    Write-Host "❌ Impossible de récupérer les logs" -ForegroundColor Red
}

# 6. Test rapide des données
Write-Host "`n🔍 Test rapide des métriques Docker..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
try {
    $dockerQuery = @{
        query = @{
            bool = @{
                must = @(
                    @{ exists = @{ field = "docker" } }
                )
            }
        }
    } | ConvertTo-Json -Depth 5

    $result = Invoke-WebRequest -Uri "http://localhost:9200/metricbeat-*/_count" -Method POST -Body $dockerQuery -ContentType "application/json" -UseBasicParsing
    $count = ($result.Content | ConvertFrom-Json).count
    
    if ($count -gt 0) {
        Write-Host "✅ $count métriques Docker trouvées!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Aucune métrique Docker encore... (attendez 2-3 minutes)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Erreur lors du test: $_" -ForegroundColor Red
}

Write-Host "`n🎯 ÉTAPES SUIVANTES:" -ForegroundColor Green
Write-Host "1. Attendez 2-3 minutes pour que les données arrivent" -ForegroundColor White
Write-Host "2. Allez dans Kibana > Management > Data Views" -ForegroundColor White
Write-Host "3. Rafraîchissez votre dataview avec le bouton 🔄" -ForegroundColor White
Write-Host "4. Vérifiez dans Discover que docker.container.name est maintenant disponible" -ForegroundColor White 