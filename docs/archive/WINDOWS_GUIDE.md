# Guide Windows - Comment Lancer le Projet

## Problème avec PowerShell

PowerShell bloque l'exécution des scripts `.bat` par défaut. Voici plusieurs solutions :

## Solution 1: Utiliser l'Invite de Commande (cmd.exe) - RECOMMANDÉ

1. Ouvrez l'**Invite de commande** (cmd.exe) - **PAS PowerShell**
2. Naviguez vers le projet :
   ```cmd
   cd E:\mistraltune
   ```
3. Lancez le script :
   ```cmd
   LANCEZ_MOI.bat all
   ```

Ou double-cliquez directement sur `LANCEZ_MOI.bat` dans l'explorateur Windows.

## Solution 2: Utiliser PowerShell avec cmd

Dans PowerShell, utilisez :

```powershell
cmd /c "cd /d E:\mistraltune && LANCEZ_MOI.bat all"
```

## Solution 3: Autoriser l'exécution de scripts PowerShell

Si vous voulez utiliser `run_all.ps1` directement :

```powershell
# Autoriser l'exécution (une seule fois, en tant qu'administrateur)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Puis utiliser
.\run_all.ps1 -All
```

## Commandes Disponibles

### Avec LANCEZ_MOI.bat (depuis cmd.exe)

```cmd
LANCEZ_MOI.bat all          # Backend + Frontend
LANCEZ_MOI.bat backend       # Backend uniquement
LANCEZ_MOI.bat frontend      # Frontend uniquement
LANCEZ_MOI.bat train         # Training (demo)
```

### Avec run_all.ps1 (si PowerShell autorisé)

```powershell
.\run_all.ps1 -All
.\run_all.ps1 -Backend
.\run_all.ps1 -Frontend
.\run_all.ps1 -Train
.\run_all.ps1 -Train -ModelPath .\models\mistral-7b
```

## Solution Rapide - Double-Clic

**La solution la plus simple** : Double-cliquez sur `LANCEZ_MOI.bat` dans l'explorateur Windows, puis tapez `all` quand demandé.

## Dépannage

### "Le script ne se lance pas"
- Utilisez **cmd.exe** au lieu de PowerShell
- Ou double-cliquez sur `LANCEZ_MOI.bat`

### "Python not found"
- Assurez-vous que Python est installé et dans le PATH
- Ou utilisez le chemin complet vers Python

### "Node not found"
- Assurez-vous que Node.js est installé
- Redémarrez le terminal après installation

## Alternative: Commandes Manuelles

Si les scripts ne fonctionnent pas, vous pouvez lancer manuellement :

### Backend
```cmd
cd E:\mistraltune
.venv\Scripts\activate
python src\api\main.py
```

### Frontend
```cmd
cd E:\mistraltune\frontend
npm run dev
```

### Training
```cmd
cd E:\mistraltune
.venv\Scripts\activate
python src\train_qlora.py --config configs\sample.yaml --lora configs\sample_lora.yaml
```

