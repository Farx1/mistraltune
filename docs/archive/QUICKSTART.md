# Quick Start Guide

Guide rapide pour lancer tout le projet et tester avec un modèle local.

## Script de Lancement Complet

### Linux/Mac

```bash
# Lancer backend + frontend
./run_all.sh --all

# Lancer uniquement le backend
./run_all.sh --backend

# Lancer uniquement le frontend
./run_all.sh --frontend

# Lancer le training (demo)
./run_all.sh --train

# Lancer le training avec un modèle local
./run_all.sh --train --model-path ./models/mistral-7b
```

### Windows

**Option 1: Script PowerShell (Recommandé)**

```powershell
# Lancer backend + frontend
.\run_all.ps1 -All

# Lancer uniquement le backend
.\run_all.ps1 -Backend

# Lancer uniquement le frontend
.\run_all.ps1 -Frontend

# Lancer le training (demo)
.\run_all.ps1 -Train

# Lancer le training avec un modèle local
.\run_all.ps1 -Train -ModelPath .\models\mistral-7b
```

**Option 2: Script Batch Simple**

```batch
REM Lancer backend + frontend
LANCEZ_MOI.bat all

REM Lancer uniquement le backend
LANCEZ_MOI.bat backend

REM Lancer uniquement le frontend
LANCEZ_MOI.bat frontend

REM Lancer le training (demo)
LANCEZ_MOI.bat train
```

**Note**: Si PowerShell bloque l'exécution, utilisez `LANCEZ_MOI.bat` qui contourne cette restriction.

## Utiliser un Modèle Local Déjà Téléchargé

### Option 1: Via le Script de Lancement

```bash
# Linux/Mac
./run_all.sh --train --model-path /chemin/vers/votre/modele

# Windows
run_all.bat --train --model-path C:\chemin\vers\votre\modele
```

### Option 2: Via la Configuration

1. Éditez `configs/local_model.yaml` et changez `base_model`:

```yaml
base_model: "./models/mistral-7b"  # Votre chemin local
```

2. Lancez le training:

```bash
python src/train_qlora.py --config configs/local_model.yaml --lora configs/sample_lora.yaml
```

### Option 3: Via l'Argument de Commande

Le script de training accepte aussi un modèle local directement dans la config YAML. Il suffit de mettre le chemin local au lieu d'un ID HuggingFace.

## Structure du Modèle Local

Votre modèle local doit avoir cette structure:

```
models/
  mistral-7b/
    ├── config.json
    ├── tokenizer_config.json
    ├── tokenizer.json
    ├── model.safetensors (ou model.bin)
    └── ...
```

## Exemples Complets

### Exemple 1: Lancer Tout (Backend + Frontend)

```bash
# Terminal 1: Lancer tout
./run_all.sh --all

# Accéder à:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Exemple 2: Training avec Modèle Local

```bash
# Si votre modèle est dans ./models/mistral-7b
./run_all.sh --train --model-path ./models/mistral-7b

# Le script va:
# 1. Créer une config temporaire avec votre modèle local
# 2. Lancer le training
# 3. Évaluer le modèle
# 4. Sauvegarder les résultats
```

### Exemple 3: Training Manuel avec Modèle Local

```bash
# 1. Éditer configs/local_model.yaml
#    base_model: "./models/mistral-7b"

# 2. Lancer le training
python src/train_qlora.py \
    --config configs/local_model.yaml \
    --lora configs/sample_lora.yaml \
    --output_dir outputs/local_run

# 3. Évaluer
python src/eval_em_f1.py \
    --model_path outputs/local_run \
    --eval_file data/sample_eval.jsonl \
    --is_adapter \
    --save_results
```

## Détection Automatique du Modèle de Base

Quand vous évaluez un adaptateur, le script détecte automatiquement le modèle de base depuis les métadonnées sauvegardées. Si vous avez utilisé un modèle local, il sera automatiquement détecté.

Pour forcer un modèle de base spécifique:

```bash
python src/eval_em_f1.py \
    --model_path outputs/local_run \
    --eval_file data/sample_eval.jsonl \
    --is_adapter \
    --base_model ./models/mistral-7b \
    --save_results
```

## Formats de Modèles Supportés

- Modèles HuggingFace (via ID): `mistralai/Mistral-7B-Instruct-v0.3`
- Modèles locaux (via chemin): `./models/mistral-7b` ou `/chemin/absolu/vers/modele`
- Modèles dans le cache HuggingFace: Automatiquement détectés

## Aide

Pour voir toutes les options:

```bash
./run_all.sh --help
# ou
run_all.bat --help
```

