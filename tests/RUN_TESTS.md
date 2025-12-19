# Guide d'Exécution des Tests

## Installation des Dépendances

```bash
pip install -r requirements.txt
```

## Exécution Rapide

```bash
# Tests de base (recommandé pour vérification rapide)
pytest tests/test_basic_functionality.py tests/test_database.py -v

# Tous les tests
pytest tests/ -v

# Tests avec rapport de couverture
pytest --cov=src --cov-report=term-missing
```

## Tests par Catégorie

### Tests de Fonctionnalité de Base
```bash
pytest tests/test_basic_functionality.py -v
```
Vérifie que les endpoints principaux répondent correctement.

### Tests de Base de Données
```bash
pytest tests/test_database.py -v
```
Vérifie les modèles, les relations et les opérations CRUD.

### Tests de Stockage
```bash
pytest tests/test_storage.py -v
```
Vérifie le système de stockage (S3/local).

### Tests d'Authentification
```bash
pytest tests/test_auth.py -v
```
Vérifie le hachage de mots de passe et JWT.

## Options Utiles

```bash
# Mode verbeux avec sortie détaillée
pytest -v -s

# Arrêter au premier échec
pytest -x

# Exécuter seulement les tests marqués "unit"
pytest -m unit

# Générer un rapport HTML
pytest --cov=src --cov-report=html
# Puis ouvrir htmlcov/index.html
```

## Vérification Rapide

Pour vérifier rapidement que tout fonctionne :

```bash
pytest tests/test_basic_functionality.py::test_health_check -v
```

Ce test vérifie que l'API répond et que la base de données est accessible.

## Résolution de Problèmes

### Erreur d'import
Si vous voyez des erreurs d'import, assurez-vous d'être dans le répertoire racine du projet :
```bash
cd E:\mistraltune
pytest
```

### Base de données verrouillée (Windows)
Les tests nettoient automatiquement les fichiers temporaires. Si vous voyez des erreurs de permission, attendez quelques secondes et réessayez.

### Tests qui échouent
Vérifiez que :
1. Toutes les dépendances sont installées
2. Vous êtes dans le bon répertoire
3. Aucun processus n'utilise la base de données de test

