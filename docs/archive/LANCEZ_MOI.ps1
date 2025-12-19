# Wrapper PowerShell pour LANCEZ_MOI.bat
# Ce script permet d'appeler le batch depuis PowerShell avec les arguments correctement passés

param(
    [Parameter(Position=0)]
    [string]$Action = ""
)

if ($Action -eq "") {
    Write-Host "=== MistralTune - Lancement Complet ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\LANCEZ_MOI.ps1 [ACTION]"
    Write-Host ""
    Write-Host "Actions:"
    Write-Host "  all       - Lancer backend + frontend"
    Write-Host "  backend   - Lancer uniquement le backend"
    Write-Host "  frontend  - Lancer uniquement le frontend"
    Write-Host "  train     - Lancer le training (demo)"
    Write-Host ""
    Write-Host "Exemples:"
    Write-Host "  .\LANCEZ_MOI.ps1 all"
    Write-Host "  .\LANCEZ_MOI.ps1 train"
    exit 0
}

# Valider l'action
$validActions = @("all", "backend", "frontend", "train")
if ($Action -notin $validActions) {
    Write-Host "Erreur: Action inconnue '$Action'" -ForegroundColor Red
    Write-Host "Actions valides: $($validActions -join ', ')"
    exit 1
}

# Appeler le script batch avec l'argument
& cmd /c "cd /d $PWD && LANCEZ_MOI.bat $Action"

