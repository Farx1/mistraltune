# Guide de Dépannage - MistralTune

## Problème: "Failed to fetch" sur le frontend

### Cause
Le backend n'est pas démarré ou n'est pas accessible.

### Solution

#### 1. Vérifier que le backend est démarré

```bash
# Vérifier si le port 8000 est utilisé
netstat -ano | findstr :8000
```

Si rien n'apparaît, le backend n'est pas démarré.

#### 2. Démarrer le backend

**Option A: Utiliser le script de démarrage**
```bash
python scripts/start_backend.py
```

**Option B: Démarrer manuellement**
```bash
# Activer l'environnement virtuel (si vous en avez un)
# .venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Démarrer le serveur
python -m uvicorn src.api.main:app --reload --port 8000
```

**Option C: Utiliser le script de démarrage unifié**
```powershell
.\start.ps1
```

#### 3. Vérifier que le backend répond

Dans un nouveau terminal:
```bash
python scripts/check_backend.py
```

Ou manuellement:
```bash
curl http://localhost:8000/api/health
```

Vous devriez voir une réponse JSON avec `"status": "healthy"`.

#### 4. Vérifier la configuration du frontend

Le frontend doit pointer vers `http://localhost:8000` par défaut.

Vérifiez que `frontend/lib/api.ts` contient:
```typescript
const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
```

#### 5. Vérifier CORS

Le backend doit avoir CORS configuré. Vérifiez `src/api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En dev, OK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Ordre de démarrage recommandé

1. **D'abord le backend** (port 8000)
   ```bash
   python scripts/start_backend.py
   ```

2. **Ensuite le frontend** (port 3000)
   ```bash
   cd frontend
   npm run dev
   ```

3. **Vérifier** que les deux sont accessibles:
   - Backend: http://localhost:8000/api/health
   - Frontend: http://localhost:3000

### Problèmes courants

#### Port déjà utilisé
```bash
# Windows: trouver le processus
netstat -ano | findstr :8000
# Tuer le processus (remplacer PID)
taskkill /PID <PID> /F
```

#### Base de données non initialisée
```bash
# Initialiser la base de données
python -m alembic upgrade head
```

#### Erreurs d'import
```bash
# Vérifier que vous êtes dans le bon répertoire
cd E:\mistraltune

# Vérifier les dépendances
pip install -r requirements.txt
```

### Vérification complète

Exécutez ce script pour vérifier tout:
```bash
python scripts/check_backend.py
```

Si tout est OK, vous verrez:
```
✅ Backend accessible!
   Status: healthy
   Database: connected
```

## Autres problèmes

### Frontend ne se compile pas
```bash
cd frontend
npm install
npm run build
```

### Erreurs de base de données
```bash
# Réinitialiser la base de données (ATTENTION: supprime les données)
rm data/jobs.db
python -m alembic upgrade head
```

### Problèmes de dépendances
```bash
# Réinstaller toutes les dépendances
pip install -r requirements.txt --force-reinstall
cd frontend
npm install
```

