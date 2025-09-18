# Script pour corriger localhost - À exécuter en tant qu'administrateur
param(
    [switch]$Force
)

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "❌ Ce script doit être exécuté en tant qu'administrateur" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pour corriger localhost, suivez ces étapes :" -ForegroundColor Yellow
    Write-Host "1. Appuyez sur Windows + X"
    Write-Host "2. Sélectionnez 'Windows PowerShell (Admin)'"
    Write-Host "3. Naviguez vers ce dossier: cd 'C:\Users\asus\projet pfa\pfefinal'"
    Write-Host "4. Exécutez: .\fix-localhost-admin.ps1"
    Write-Host ""
    Write-Host "Ou bien, manuellement :"
    Write-Host "1. Ouvrez le Bloc-notes en tant qu'administrateur"
    Write-Host "2. Ouvrez: C:\Windows\System32\drivers\etc\hosts"
    Write-Host "3. Ajoutez ces lignes à la fin :"
    Write-Host "   127.0.0.1       localhost"
    Write-Host "   ::1             localhost"
    Write-Host "4. Sauvegardez"
    
    Read-Host "Appuyez sur Entrée pour continuer"
    return
}

$hostsPath = "C:\Windows\System32\drivers\etc\hosts"

Write-Host "🔧 Correction du fichier hosts pour localhost..." -ForegroundColor Green

# Sauvegarde
Copy-Item $hostsPath "$hostsPath.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')" -Force
Write-Host "✅ Sauvegarde créée" -ForegroundColor Green

# Lecture du fichier
$content = Get-Content $hostsPath

# Vérification si localhost existe déjà
$hasLocalhost = $false
$hasLocalhostIPv6 = $false

foreach ($line in $content) {
    if ($line -match "^127\.0\.0\.1\s+localhost\s*$") {
        $hasLocalhost = $true
    }
    if ($line -match "^::1\s+localhost\s*$") {
        $hasLocalhostIPv6 = $true
    }
}

$newContent = @()
$modified = $false

# Traitement du contenu
foreach ($line in $content) {
    # Décommenter les lignes localhost si elles sont commentées
    if ($line -match "^#\s*127\.0\.0\.1\s+localhost") {
        $newContent += "127.0.0.1       localhost"
        $hasLocalhost = $true
        $modified = $true
        Write-Host "✅ Ligne IPv4 localhost décommentée" -ForegroundColor Green
    }
    elseif ($line -match "^#\s*::1\s+localhost") {
        $newContent += "::1             localhost"
        $hasLocalhostIPv6 = $true
        $modified = $true
        Write-Host "✅ Ligne IPv6 localhost décommentée" -ForegroundColor Green
    }
    else {
        $newContent += $line
    }
}

# Ajouter localhost s'il n'existe pas
if (-not $hasLocalhost) {
    $newContent += "127.0.0.1       localhost"
    $modified = $true
    Write-Host "✅ Ligne IPv4 localhost ajoutée" -ForegroundColor Green
}

if (-not $hasLocalhostIPv6) {
    $newContent += "::1             localhost"
    $modified = $true
    Write-Host "✅ Ligne IPv6 localhost ajoutée" -ForegroundColor Green
}

if ($modified) {
    # Écriture du fichier
    $newContent | Set-Content $hostsPath -Encoding ASCII
    Write-Host "✅ Fichier hosts mis à jour avec succès!" -ForegroundColor Green
    
    # Vider le cache DNS
    Write-Host "🔄 Vidage du cache DNS..." -ForegroundColor Yellow
    ipconfig /flushdns | Out-Null
    Write-Host "✅ Cache DNS vidé" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "🎉 LOCALHOST CORRIGÉ AVEC SUCCÈS!" -ForegroundColor Green
    Write-Host "Vous pouvez maintenant utiliser http://localhost" -ForegroundColor Cyan
    Write-Host "Redémarrez votre navigateur pour que les changements prennent effet." -ForegroundColor Yellow
} else {
    Write-Host "ℹ️ Localhost est déjà configuré correctement" -ForegroundColor Blue
}

Write-Host ""
Write-Host "Test de connectivité :"
try {
    $test = Test-NetConnection -ComputerName localhost -Port 80 -WarningAction SilentlyContinue
    if ($test.TcpTestSucceeded) {
        Write-Host "✅ http://localhost:80 - Connexion réussie" -ForegroundColor Green
    } else {
        Write-Host "❌ http://localhost:80 - Échec de connexion" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Erreur lors du test de connectivité" -ForegroundColor Red
}

Read-Host "Appuyez sur Entrée pour continuer"
