# Usage Guide - Script de Lancement Complet

## Vue d'ensemble

Le projet inclut maintenant un script de lancement complet (`run_all.sh` / `run_all.bat`) qui permet de lancer facilement tous les composants du projet.

## Commandes Principales

### Lancer Backend + Frontend

```bash
# Linux/Mac
./run_all.sh --all

# Windows
run_all.bat --all
```

Cela démarre :
- Backend API sur `http://localhost:8000`
- Frontend sur `http://localhost:3000`
- Documentation API sur `http://localhost:8000/docs`

### Lancer uniquement le Backend

```bash
./run_all.sh --backend
# ou
run_all.bat --backend
```

### Lancer uniquement le Frontend

```bash
./run_all.sh --frontend
# ou
run_all.bat --frontend
```

### Lancer le Training (Demo)

```bash
./run_all.sh --train
# ou
run_all.bat --train
```

Lance un training complet avec les données d'exemple :
1. Training sur `data/sample_train.jsonl`
2. Évaluation sur `data/sample_eval.jsonl`
3. Sauvegarde des résultats

## Utiliser un Modèle Local

### Option 1: Via le Script (Recommandé)

```bash
# Linux/Mac
./run_all.sh --train --model-path ./models/mistral-7b

# Windows
run_all.bat --train --model-path .\models\mistral-7b
```

Le script crée automatiquement une configuration temporaire avec votre modèle local.

### Option 2: Via la Configuration

1. Éditez `configs/local_model.yaml` :

```yaml
base_model: "./models/mistral-7b"  # Votre chemin local
```

2. Lancez le training :

```bash
python src/train_qlora.py --config configs/local_model.yaml --lora configs/sample_lora.yaml
```

### Option 3: Modifier une Config Existante

Vous pouvez modifier n'importe quelle config YAML pour utiliser un modèle local :

```yaml
# Dans configs/base.yaml ou configs/sample.yaml
base_model: "./models/mistral-7b"  # Au lieu de "mistralai/Mistral-7B-Instruct-v0.3"
```

## Structure du Modèle Local

Votre modèle doit être dans un dossier avec cette structure :

```
models/
  mistral-7b/
    ├── config.json
    ├── tokenizer_config.json
    ├── tokenizer.json
    ├── model.safetensors (ou model.bin)
    └── ...
```

Ou simplement le chemin vers un modèle téléchargé via HuggingFace :

```
~/.cache/huggingface/hub/models--mistralai--Mistral-7B-Instruct-v0.3/
```

## Détection Automatique du Modèle de Base

Quand vous évaluez un adaptateur, le script détecte automatiquement le modèle de base depuis les métadonnées sauvegardées lors du training.

Si vous avez utilisé un modèle local pour le training, il sera automatiquement détecté lors de l'évaluation.

Pour forcer un modèle spécifique :

```bash
python src/eval_em_f1.py \
    --model_path outputs/demo_run \
    --eval_file data/sample_eval.jsonl \
    --is_adapter \
    --base_model ./models/mistral-7b \
    --save_results
```

## Exemples Complets

### Exemple 1: Pipeline Complet avec Modèle Local

```bash
# 1. Training avec modèle local
./run_all.sh --train --model-path ./models/mistral-7b

# 2. Évaluation (détection automatique du modèle de base)
python src/eval_em_f1.py \
    --model_path outputs/demo_run \
    --eval_file data/sample_eval.jsonl \
    --is_adapter \
    --save_results
```

### Exemple 2: Backend + Frontend + Training

```bash
# Terminal 1: Lancer services
./run_all.sh --all

# Terminal 2: Lancer training
./run_all.sh --train --model-path ./models/mistral-7b
```

### Exemple 3: Training Manuel avec Modèle Local

```bash
# 1. Créer/modifier config
cat > configs/my_local.yaml << EOF
base_model: "./models/mistral-7b"
train_file: "data/train.jsonl"
eval_file: "data/val.jsonl"
output_dir: "outputs/my_run"
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 1e-4
num_train_epochs: 3
logging_steps: 10
eval_steps: 200
save_steps: 500
bnb_4bit: true
fp16: true
max_seq_length: 2048
packing: true
seed: 42
EOF

# 2. Training
python src/train_qlora.py \
    --config configs/my_local.yaml \
    --lora configs/lora_r16a32.yaml

# 3. Évaluation
python src/eval_em_f1.py \
    --model_path outputs/my_run \
    --eval_file data/val.jsonl \
    --is_adapter \
    --save_results
```

## Formats de Modèles Supportés

- **HuggingFace ID**: `mistralai/Mistral-7B-Instruct-v0.3` (téléchargement automatique)
- **Chemin local relatif**: `./models/mistral-7b`
- **Chemin local absolu**: `/home/user/models/mistral-7b` ou `C:\models\mistral-7b`
- **Cache HuggingFace**: Détecté automatiquement si le modèle est dans le cache

## Aide

Pour voir toutes les options disponibles :

```bash
./run_all.sh --help
# ou
run_all.bat --help
```

## Notes Importantes

1. **Modèle Local**: Assurez-vous que votre modèle local est compatible avec Mistral (même architecture de tokenizer)

2. **Détection Automatique**: Le script d'évaluation détecte automatiquement le modèle de base depuis `training_metadata.yaml` ou `config_used.yaml`

3. **GPU**: Le training est beaucoup plus rapide avec GPU. Le script vous avertira si aucun GPU n'est détecté.

4. **Premier Lancement**: Au premier lancement, les dépendances seront installées automatiquement si nécessaire.

