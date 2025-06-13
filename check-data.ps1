# Script pour vérifier les données Metricbeat
Write-Host "🔍 Vérification des données Metricbeat..." -ForegroundColor Green

try {
    # Vérifier les index
    Write-Host "`n📊 Index disponibles:" -ForegroundColor Yellow
    $indices = Invoke-WebRequest -Uri "http://localhost:9200/_cat/indices/metricbeat*?v" -UseBasicParsing
    Write-Host $indices.Content

    # Récupérer un exemple de document
    Write-Host "`n📄 Exemple de document:" -ForegroundColor Yellow
    $sample = Invoke-WebRequest -Uri "http://localhost:9200/metricbeat-*/_search?size=1" -UseBasicParsing
    $sampleJson = $sample.Content | ConvertFrom-Json
    
    if ($sampleJson.hits.total.value -gt 0) {
        $doc = $sampleJson.hits.hits[0]._source
        Write-Host "✅ Document trouvé avec les champs suivants:" -ForegroundColor Green
        
        # Afficher les champs principaux
        if ($doc.system) {
            Write-Host "  🖥️  system.cpu.total.pct: $($doc.system.cpu.total.pct)" -ForegroundColor Cyan
            Write-Host "  🖥️  system.memory.used.pct: $($doc.system.memory.used.pct)" -ForegroundColor Cyan
            Write-Host "  🖥️  system.load.1: $($doc.system.load.'1')" -ForegroundColor Cyan
        }
        
        if ($doc.docker) {
            Write-Host "  🐳 docker.container.name: $($doc.docker.container.name)" -ForegroundColor Blue
            Write-Host "  🐳 docker.cpu.total.pct: $($doc.docker.cpu.total.pct)" -ForegroundColor Blue
            Write-Host "  🐳 docker.memory.usage.pct: $($doc.docker.memory.usage.pct)" -ForegroundColor Blue
        }
        
        Write-Host "  ⏰ @timestamp: $($doc.'@timestamp')" -ForegroundColor Magenta
        
    } else {
        Write-Host "❌ Aucun document trouvé" -ForegroundColor Red
    }

    # Vérifier le mapping des champs
    Write-Host "`n🗺️  Mapping des champs principaux:" -ForegroundColor Yellow
    $mapping = Invoke-WebRequest -Uri "http://localhost:9200/metricbeat-*/_mapping" -UseBasicParsing
    Write-Host "✅ Mapping récupéré (vérifiez dans Kibana > Dev Tools)" -ForegroundColor Green

} catch {
    Write-Host "❌ Erreur: $_" -ForegroundColor Red
}

Write-Host "`n🎯 Instructions pour Kibana:" -ForegroundColor Green
Write-Host "1. Allez dans Management > Stack Management > Data Views" -ForegroundColor White
Write-Host "2. Sélectionnez votre dataview 'metricbeat-*'" -ForegroundColor White
Write-Host "3. Cliquez sur 'Refresh field list' (🔄)" -ForegroundColor White
Write-Host "4. Allez dans Analytics > Lens pour créer des visualisations" -ForegroundColor White 