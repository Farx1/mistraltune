#!/usr/bin/env python3
"""
Script simple pour tester la connexion frontend-backend.
"""

import requests
import sys

def test_connection():
    """Test la connexion au backend."""
    url = "http://localhost:8000"
    
    print("Test de connexion au backend...")
    print(f"URL: {url}")
    print()
    
    try:
        # Test health endpoint
        print("1. Test /api/health...")
        response = requests.get(f"{url}/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend accessible!")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database', 'unknown')}")
        else:
            print(f"   ❌ Code: {response.status_code}")
            return False
        
        # Test jobs endpoint
        print("\n2. Test /api/jobs...")
        response = requests.get(f"{url}/api/jobs", timeout=5)
        if response.status_code == 200:
            print("   ✅ Endpoint jobs accessible!")
            data = response.json()
            print(f"   Nombre de jobs: {len(data.get('jobs', []))}")
        else:
            print(f"   ❌ Code: {response.status_code}")
            return False
        
        # Test datasets endpoint
        print("\n3. Test /api/datasets...")
        response = requests.get(f"{url}/api/datasets", timeout=5)
        if response.status_code == 200:
            print("   ✅ Endpoint datasets accessible!")
            data = response.json()
            print(f"   Nombre de datasets: {len(data.get('datasets', []))}")
        else:
            print(f"   ❌ Code: {response.status_code}")
            return False
        
        print("\n✅ Tous les tests de connexion ont réussi!")
        print("\nLe backend est prêt. Vous pouvez maintenant démarrer le frontend.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au backend")
        print("\nLe backend n'est pas démarré.")
        print("\nPour démarrer le backend:")
        print("  python scripts/start_backend.py")
        print("\nOu manuellement:")
        print("  python -m uvicorn src.api.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

