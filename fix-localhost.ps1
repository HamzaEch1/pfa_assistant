# Fix localhost resolution
$hostsPath = "C:\Windows\System32\drivers\etc\hosts"

# Backup the original hosts file
Copy-Item $hostsPath "$hostsPath.backup" -Force

# Read the current hosts file
$hostsContent = Get-Content $hostsPath

# Check if localhost entries exist and are uncommented
$hasLocalhost = $false
$hasLocalhostIPv6 = $false

foreach ($line in $hostsContent) {
    if ($line -match "^127\.0\.0\.1\s+localhost") {
        $hasLocalhost = $true
    }
    if ($line -match "^::1\s+localhost") {
        $hasLocalhostIPv6 = $true
    }
}

# If localhost entries don't exist or are commented, add them
$newContent = @()
foreach ($line in $hostsContent) {
    # Uncomment localhost lines if they're commented
    if ($line -match "^#\s*127\.0\.0\.1\s+localhost") {
        $newContent += "127.0.0.1       localhost"
        $hasLocalhost = $true
    }
    elseif ($line -match "^#\s*::1\s+localhost") {
        $newContent += "::1             localhost"
        $hasLocalhostIPv6 = $true
    }
    else {
        $newContent += $line
    }
}

# Add localhost entries if they don't exist
if (-not $hasLocalhost) {
    $newContent += "127.0.0.1       localhost"
}
if (-not $hasLocalhostIPv6) {
    $newContent += "::1             localhost"
}

# Write the updated content back to hosts file
$newContent | Set-Content $hostsPath -Encoding ASCII

Write-Host "Fichier hosts mis à jour avec succès!"
Write-Host "Localhost devrait maintenant fonctionner."
