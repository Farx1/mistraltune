#!/usr/bin/env python3
"""
Script pour démarrer le backend FastAPI.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def start_backend():
    """Démarre le backend FastAPI."""
    print("Démarrage du backend MistralTune...")
    
    # Vérifier que nous sommes dans le bon répertoire
    if not Path("src/api/main.py").exists():
        print("ERREUR: Doit être exécuté depuis la racine du projet")
        sys.exit(1)
    
    # Vérifier que la base de données est initialisée
    print("Initialisation de la base de données...")
    try:
        from src.db.database import init_db
        init_db()
        print("Base de données initialisée")
    except Exception as e:
        print(f"AVERTISSEMENT: Erreur lors de l'initialisation de la DB: {e}")
        print("Le backend démarrera quand même...")
    
    # Démarrer uvicorn
    port = int(os.getenv("BACKEND_PORT", "8000"))
    print(f"Démarrage du serveur sur le port {port}...")
    print(f"API disponible sur: http://localhost:{port}")
    print(f"Documentation sur: http://localhost:{port}/docs")
    print("\nAppuyez sur Ctrl+C pour arrêter le serveur\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
    except Exception as e:
        print(f"ERREUR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_backend()

