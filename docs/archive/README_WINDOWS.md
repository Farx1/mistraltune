# Guide Rapide Windows

## 🚀 Lancer Tout le Projet

### Méthode la Plus Simple

1. **Double-cliquez** sur `LANCEZ_MOI.bat` dans l'explorateur Windows
2. Tapez `all` et appuyez sur Entrée

C'est tout ! Le backend et le frontend vont démarrer.

### Depuis l'Invite de Commande (cmd.exe)

```cmd
cd E:\mistraltune
LANCEZ_MOI.bat all
```

## 📋 Options Disponibles

```cmd
LANCEZ_MOI.bat all          # Backend + Frontend
LANCEZ_MOI.bat backend       # Backend uniquement  
LANCEZ_MOI.bat frontend      # Frontend uniquement
LANCEZ_MOI.bat train         # Training (demo)
```

## 🎯 Utiliser un Modèle Local

Pour utiliser un modèle Mistral déjà téléchargé :

1. Éditez `configs/local_model.yaml`
2. Changez `base_model` vers votre chemin local :
   ```yaml
   base_model: "C:\models\mistral-7b"  # Votre chemin
   ```
3. Lancez le training :
   ```cmd
   python src\train_qlora.py --config configs\local_model.yaml --lora configs\sample_lora.yaml
   ```

## ⚠️ Important

- Utilisez **cmd.exe** (Invite de commande), **PAS PowerShell**
- Ou double-cliquez directement sur `LANCEZ_MOI.bat`

## 🔗 URLs

Une fois lancé :
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📚 Plus d'Infos

Voir [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) pour plus de détails et dépannage.

