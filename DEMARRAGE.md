# 🚀 Guide de Démarrage - MistralTune

## ⚠️ Problème: "Failed to fetch" sur le frontend

**Cause**: Le backend n'est pas démarré ou n'est pas accessible.

## ✅ Solution Rapide

### Étape 1: Démarrer le Backend

Ouvrez un terminal PowerShell dans le dossier du projet et exécutez:

```powershell
python scripts/start_backend.py
```

**OU** manuellement:

```powershell
python -m uvicorn src.api.main:app --reload --port 8000
```

Vous devriez voir:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Étape 2: Vérifier que le Backend fonctionne

Dans un **nouveau terminal**, testez:

```powershell
python scripts/check_backend.py
```

Ou ouvrez dans votre navigateur: http://localhost:8000/api/health

Vous devriez voir: `{"status":"healthy",...}`

### Étape 3: Démarrer le Frontend

Dans un **nouveau terminal**:

```powershell
cd frontend
npm run dev
```

### Étape 4: Accéder à l'application

Ouvrez http://localhost:3000 dans votre navigateur.

## 🔍 Vérifications

### Le backend est-il démarré?

```powershell
# Vérifier si le port 8000 est utilisé
netstat -ano | findstr :8000
```

Si vous voyez une ligne, le backend tourne.

### Le backend répond-il?

```powershell
# Test rapide
curl http://localhost:8000/api/health
```

Ou dans votre navigateur: http://localhost:8000/api/health

### Erreurs courantes

#### "Port 8000 already in use"
```powershell
# Trouver le processus
netstat -ano | findstr :8000
# Tuer le processus (remplacer PID par le numéro trouvé)
taskkill /PID <PID> /F
```

#### "Module not found"
```powershell
# Installer les dépendances
pip install -r requirements.txt
```

#### "Database error"
```powershell
# Initialiser la base de données
python -m alembic upgrade head
```

## 📋 Ordre de démarrage IMPORTANT

1. ✅ **D'abord**: Backend (port 8000)
2. ✅ **Ensuite**: Frontend (port 3000)
3. ✅ **Enfin**: Ouvrir le navigateur

**Les deux serveurs doivent tourner en même temps!**

## 🎯 Démarrage Automatique (Recommandé)

Utilisez le script de démarrage unifié:

```powershell
.\start.ps1
```

Ce script démarre automatiquement le backend ET le frontend.

## 💡 Astuce

Gardez deux terminaux ouverts:
- **Terminal 1**: Backend (ne pas fermer)
- **Terminal 2**: Frontend (ne pas fermer)

Si vous fermez un terminal, le serveur correspondant s'arrête.

