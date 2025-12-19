# Tests pour MistralTune

Cette suite de tests vérifie que l'application fonctionne correctement et qu'un utilisateur peut l'utiliser convenablement.

## Structure des tests

- `test_database.py` - Tests des modèles de base de données et opérations
- `test_api_endpoints.py` - Tests des endpoints API REST
- `test_user_workflows.py` - Tests end-to-end des workflows utilisateur
- `test_storage.py` - Tests du système de stockage (S3/local)
- `test_auth.py` - Tests d'authentification et autorisation

## Exécution des tests

### Tous les tests
```bash
pytest
```

### Tests spécifiques
```bash
pytest tests/test_api_endpoints.py
pytest tests/test_user_workflows.py
```

### Avec couverture
```bash
pytest --cov=src --cov-report=html
```

### Tests marqués
```bash
pytest -m unit          # Tests unitaires uniquement
pytest -m integration    # Tests d'intégration
pytest -m e2e           # Tests end-to-end
```

## Workflows testés

1. **Upload de dataset** : Upload → Validation → Stockage → Versioning
2. **Création de job** : Création → Queue → Exécution → Suivi
3. **Gestion des logs** : Création → Stockage → Récupération
4. **Filtrage et recherche** : Liste → Filtres → Détails
5. **Annulation de job** : Détection → Annulation → Vérification

## Configuration

Les tests utilisent :
- Base de données SQLite temporaire
- Mode DEMO activé (pas d'appels API réels)
- Authentification désactivée par défaut
- Stockage local (pas de S3 requis)

## Notes

- Les tests sont isolés (chaque test a sa propre base de données)
- Les fichiers temporaires sont nettoyés automatiquement
- Les tests peuvent être exécutés en parallèle avec `pytest -n auto`

