# Démarrage Rapide - MistralTune

## 🚀 Démarrage en 3 étapes

### 1. Démarrer le Backend

```bash
python scripts/start_backend.py
```

Ou manuellement:
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

**Vérification**: Ouvrez http://localhost:8000/api/health dans votre navigateur.
Vous devriez voir: `{"status":"healthy",...}`

### 2. Démarrer le Frontend

Dans un **nouveau terminal**:
```bash
cd frontend
npm run dev
```

**Vérification**: Ouvrez http://localhost:3000 dans votre navigateur.

### 3. Utiliser l'application

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## ⚠️ Si vous voyez "Failed to fetch"

Cela signifie que le **backend n'est pas démarré** ou n'est pas accessible.

**Solution**:
1. Vérifiez que le backend tourne (étape 1)
2. Attendez quelques secondes que le backend soit complètement démarré
3. Rafraîchissez la page du frontend

## 🔍 Vérification rapide

```bash
# Vérifier que le backend répond
python scripts/check_backend.py

# Ou avec curl
curl http://localhost:8000/api/health
```

## 📝 Notes

- Le backend doit être démarré **avant** le frontend
- Les deux doivent tourner en même temps
- Le backend écoute sur le port **8000**
- Le frontend écoute sur le port **3000**

## 🐛 Problèmes?

Voir [TROUBLESHOOTING.md](TROUBLESHOOTING.md) pour plus de détails.

