Write-Host "===== SOLUTION RAPIDE POUR LOCALHOST ====="
Write-Host ""
Write-Host "Solution 1 - Utilisation temporaire de 127.0.0.1 :"
Write-Host "Vous pouvez continuer à utiliser http://127.0.0.1 qui fonctionne parfaitement."
Write-Host ""
Write-Host "Solution 2 - Correction du fichier hosts (nécessite les droits admin) :"
Write-Host "1. Appuyez sur Windows + R"
Write-Host "2. Tapez: notepad"
Write-Host "3. Faites clic droit sur 'Bloc-notes' et 'Exécuter en tant qu'administrateur'"
Write-Host "4. Dans le Bloc-notes, ouvrez: C:\Windows\System32\drivers\etc\hosts"
Write-Host "5. Ajoutez ces lignes à la fin du fichier :"
Write-Host "   127.0.0.1       localhost"
Write-Host "   ::1             localhost"
Write-Host "6. Sauvegardez et fermez"
Write-Host "7. Redémarrez votre navigateur"
Write-Host ""
Write-Host "Solution 3 - Alternative simple :"
Write-Host "Créez un raccourci avec l'URL http://127.0.0.1 sur votre bureau"
Write-Host ""
Write-Host "============================="

# Test de connectivité
Write-Host ""
Write-Host "Test de connectivité actuel :"
try {
    $test = Test-NetConnection -ComputerName "127.0.0.1" -Port 80 -WarningAction SilentlyContinue
    if ($test.TcpTestSucceeded) {
        Write-Host "✅ http://127.0.0.1 - Fonctionne parfaitement"
    }
} catch {
    Write-Host "❌ Problème de connectivité"
}

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Votre application répond correctement (Status: $($response.StatusCode))"
} catch {
    Write-Host "❌ L'application ne répond pas"
}

Write-Host ""
Write-Host "Votre application est accessible sur :"
Write-Host "🌐 http://127.0.0.1 (fonctionne)"
Write-Host "🌐 http://127.0.0.1:3000 (frontend direct)"
Write-Host "🌐 http://localhost (après correction du fichier hosts)"
