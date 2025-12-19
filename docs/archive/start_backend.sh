#!/bin/bash
# Script pour démarrer le backend FastAPI

# Activer l'environnement virtuel
source .venv/bin/activate

# Vérifier que la clé API est définie
if [ -z "$MISTRAL_API_KEY" ]; then
    echo "⚠️  MISTRAL_API_KEY n'est pas définie"
    echo "Définissez-la avec: export MISTRAL_API_KEY='votre-clé'"
    exit 1
fi

# Démarrer le serveur
cd src/api
python main.py

