# Script PowerShell simple pour lancer MistralTune
# Utilisez: .\LANCEZ.ps1 all
# Ou: powershell -ExecutionPolicy Bypass -File LANCEZ.ps1 all

param([string]$Action = "")

if ($Action -eq "") {
    Write-Host "=== MistralTune - Lancement Complet ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\LANCEZ.ps1 [ACTION]"
    Write-Host ""
    Write-Host "Actions:"
    Write-Host "  all       - Lancer backend + frontend"
    Write-Host "  backend   - Lancer uniquement le backend"
    Write-Host "  frontend  - Lancer uniquement le frontend"
    Write-Host "  train     - Lancer le training (demo)"
    Write-Host ""
    Write-Host "Exemples:"
    Write-Host "  .\LANCEZ.ps1 all"
    Write-Host "  .\LANCEZ.ps1 train"
    Write-Host ""
    Write-Host "Si PowerShell bloque, utilisez:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File LANCEZ.ps1 all"
    exit 0
}

# Valider l'action
$validActions = @("all", "backend", "frontend", "train")
if ($Action -notin $validActions) {
    Write-Host "Erreur: Action inconnue '$Action'" -ForegroundColor Red
    Write-Host "Actions valides: $($validActions -join ', ')"
    exit 1
}

# Vérifier qu'on est dans le bon répertoire
if (-not (Test-Path "requirements.txt")) {
    Write-Host "Erreur: Doit être exécuté depuis la racine du projet" -ForegroundColor Red
    exit 1
}

# Créer les dossiers nécessaires
@("outputs", "reports", "data") | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ | Out-Null }
}

# Fonction pour démarrer le backend
function Start-Backend {
    Write-Host "`n=== Démarrage du Backend ===" -ForegroundColor Cyan
    
    if (-not (Test-Path ".venv")) {
        Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
        python -m venv .venv
    }
    
    & ".venv\Scripts\Activate.ps1"
    
    $pythonCheck = python -c "import torch" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installation des dépendances..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
    
    Write-Host "Démarrage du backend API..." -ForegroundColor Green
    Start-Process python -ArgumentList "src\api\main.py" -WindowStyle Normal
    Start-Sleep -Seconds 2
    Write-Host "Backend démarré: http://localhost:8000" -ForegroundColor Green
    Write-Host "Documentation API: http://localhost:8000/docs" -ForegroundColor Green
}

# Fonction pour démarrer le frontend
function Start-Frontend {
    Write-Host "`n=== Démarrage du Frontend ===" -ForegroundColor Cyan
    
    if (-not (Test-Path "frontend\node_modules")) {
        Write-Host "Installation des dépendances frontend..." -ForegroundColor Yellow
        Set-Location frontend
        npm install
        Set-Location ..
    }
    
    Write-Host "Démarrage du frontend..." -ForegroundColor Green
    Set-Location frontend
    Start-Process npm -ArgumentList "run", "dev" -WindowStyle Normal
    Set-Location ..
    Write-Host "Frontend démarré: http://localhost:3000" -ForegroundColor Green
}

# Fonction pour lancer le training
function Start-Training {
    Write-Host "`n=== Lancement du Training (Demo) ===" -ForegroundColor Cyan
    
    if (-not (Test-Path "data\sample_train.jsonl") -or -not (Test-Path "data\sample_eval.jsonl")) {
        Write-Host "Erreur: Fichiers de données d'exemple non trouvés" -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path ".venv")) {
        Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
        python -m venv .venv
    }
    
    & ".venv\Scripts\Activate.ps1"
    
    $pythonCheck = python -c "import torch" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installation des dépendances..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
    
    Write-Host "`nÉtape 1: Training..." -ForegroundColor Yellow
    python src\train_qlora.py --config configs\sample.yaml --lora configs\sample_lora.yaml --output_dir outputs\demo_run
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erreur: Training échoué" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`nÉtape 2: Évaluation..." -ForegroundColor Yellow
    python src\eval_em_f1.py --model_path outputs\demo_run --eval_file data\sample_eval.jsonl --is_adapter --save_results
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erreur: Évaluation échouée" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n=== Training terminé avec succès! ===" -ForegroundColor Green
    Write-Host "Vérifiez outputs\demo_run pour l'adaptateur entraîné"
    Write-Host "Vérifiez reports\results.csv pour les métriques"
}

# Exécuter l'action demandée
switch ($Action) {
    "all" {
        Start-Backend
        Start-Frontend
        Write-Host "`n=== Services en cours d'exécution ===" -ForegroundColor Green
        Write-Host "Backend: http://localhost:8000"
        Write-Host "Frontend: http://localhost:3000"
        Write-Host "`nLes services tournent dans des fenêtres séparées."
        Write-Host "Fermez ces fenêtres pour arrêter les services."
    }
    "backend" {
        Start-Backend
    }
    "frontend" {
        Start-Frontend
    }
    "train" {
        Start-Training
    }
}

