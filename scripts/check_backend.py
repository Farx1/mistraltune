#!/usr/bin/env python3
"""
Script pour vérifier que le backend est accessible.
"""

import sys
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_backend(url="http://localhost:8000"):
    """Vérifie que le backend répond."""
    print(f"Vérification du backend à {url}...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend accessible!")
            print(f"   Status: {response.json().get('status')}")
            print(f"   Database: {response.json().get('database', 'unknown')}")
            return True
        else:
            print(f"❌ Backend répond avec le code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("ERREUR: Impossible de se connecter au backend")
        print("   Assurez-vous que le backend est demarre:")
        print("   python -m uvicorn src.api.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    import os
    api_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
    success = check_backend(api_url)
    sys.exit(0 if success else 1)

