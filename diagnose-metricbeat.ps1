# Script de diagnostic approfondi pour Metricbeat
Write-Host "🔍 DIAGNOSTIC METRICBEAT DOCKER" -ForegroundColor Green

# 1. Vérifier que tous les conteneurs fonctionnent
Write-Host "`n📦 Statut des conteneurs:" -ForegroundColor Yellow
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host $containers -ForegroundColor White
} catch {
    Write-Host "❌ Impossible de lister les conteneurs Docker" -ForegroundColor Red
}

# 2. Vérifier les logs de Metricbeat (dernières 20 lignes)
Write-Host "`n📋 Logs Metricbeat (dernières 20 lignes):" -ForegroundColor Yellow
try {
    $logs = docker logs metricbeat --tail 20 2>&1
    Write-Host $logs -ForegroundColor White
} catch {
    Write-Host "❌ Impossible de récupérer les logs de Metricbeat" -ForegroundColor Red
}

# 3. Tester l'accès à Elasticsearch
Write-Host "`n🔍 Test Elasticsearch:" -ForegroundColor Yellow
try {
    $esHealth = Invoke-WebRequest -Uri "http://localhost:9200/_cluster/health" -UseBasicParsing -ErrorAction Stop
    $healthJson = $esHealth.Content | ConvertFrom-Json
    Write-Host "✅ Elasticsearch status: $($healthJson.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Elasticsearch inaccessible: $_" -ForegroundColor Red
}

# 4. Compter les documents par type de métrique
Write-Host "`n📊 Analyse des données par type:" -ForegroundColor Yellow
try {
    # Documents système
    $systemQuery = @{
        query = @{
            bool = @{
                must = @(
                    @{ exists = @{ field = "system" } }
                )
            }
        }
    } | ConvertTo-Json -Depth 5

    $systemResult = Invoke-WebRequest -Uri "http://localhost:9200/metricbeat-*/_count" -Method POST -Body $systemQuery -ContentType "application/json" -UseBasicParsing
    $systemCount = ($systemResult.Content | ConvertFrom-Json).count
    Write-Host "  🖥️  Documents système: $systemCount" -ForegroundColor Cyan

    # Documents Docker
    $dockerQuery = @{
        query = @{
            bool = @{
                must = @(
                    @{ exists = @{ field = "docker" } }
                )
            }
        }
    } | ConvertTo-Json -Depth 5

    $dockerResult = Invoke-WebRequest -Uri "http://localhost:9200/metricbeat-*/_count" -Method POST -Body $dockerQuery -ContentType "application/json" -UseBasicParsing
    $dockerCount = ($dockerResult.Content | ConvertFrom-Json).count
    Write-Host "  🐳 Documents Docker: $dockerCount" -ForegroundColor Blue

    if ($dockerCount -eq 0) {
        Write-Host "⚠️  PROBLÈME: Aucune métrique Docker trouvée!" -ForegroundColor Red
    }

} catch {
    Write-Host "❌ Erreur lors de l'analyse des données: $_" -ForegroundColor Red
}

# 5. Vérifier un échantillon de document pour voir les champs disponibles
Write-Host "`n📄 Champs disponibles dans un échantillon:" -ForegroundColor Yellow
try {
    $sampleResult = Invoke-WebRequest -Uri "http://localhost:9200/metricbeat-*/_search?size=1" -UseBasicParsing
    $sample = ($sampleResult.Content | ConvertFrom-Json).hits.hits[0]._source
    
    Write-Host "  Champs principaux trouvés:" -ForegroundColor White
    if ($sample.system) { Write-Host "    ✅ system.*" -ForegroundColor Green }
    if ($sample.docker) { Write-Host "    ✅ docker.*" -ForegroundColor Green } else { Write-Host "    ❌ docker.* (manquant)" -ForegroundColor Red }
    if ($sample.metricset) { Write-Host "    ✅ metricset: $($sample.metricset.name)" -ForegroundColor Green }
    if ($sample.agent) { Write-Host "    ✅ agent: $($sample.agent.name)" -ForegroundColor Green }
    
} catch {
    Write-Host "❌ Impossible de récupérer un échantillon: $_" -ForegroundColor Red
}

Write-Host "`n🎯 RECOMMANDATIONS:" -ForegroundColor Green
Write-Host "1. Si 'Documents Docker: 0' -> Problème de configuration du module Docker" -ForegroundColor White
Write-Host "2. Si logs montrent des erreurs Docker -> Problème d'accès au socket Docker" -ForegroundColor White
Write-Host "3. Si seules les métriques système sont présentes -> Redémarrer avec module Docker forcé" -ForegroundColor White 