@echo off
REM Script simple pour lancer tout sur Windows
REM Utilisez ce script depuis l'invite de commande (cmd.exe) ou double-cliquez dessus

echo === MistralTune - Lancement Complet ===
echo.

REM Vérifier si on est dans le bon répertoire
if not exist "requirements.txt" (
    echo Erreur: Doit etre execute depuis la racine du projet
    pause
    exit /b 1
)

REM Vérifier les arguments
if "%1"=="" (
    echo Usage: LANCEZ_MOI.bat [OPTION]
    echo.
    echo Options:
    echo   all       - Lancer backend + frontend
    echo   backend   - Lancer uniquement le backend
    echo   frontend  - Lancer uniquement le frontend
    echo   train     - Lancer le training (demo)
    echo.
    echo Exemples:
    echo   LANCEZ_MOI.bat all
    echo   LANCEZ_MOI.bat train
    echo.
    pause
    exit /b 0
)

REM Créer les dossiers nécessaires
if not exist "outputs" mkdir outputs
if not exist "reports" mkdir reports
if not exist "data" mkdir data

REM Traiter les options
if "%1"=="all" goto start_all
if "%1"=="backend" goto start_backend
if "%1"=="frontend" goto start_frontend
if "%1"=="train" goto start_train

echo Option inconnue: %1
echo Utilisez: all, backend, frontend, ou train
pause
exit /b 1

:start_all
echo Lancement du backend et du frontend...
goto start_backend

:start_backend
echo.
echo === Démarrage du Backend ===
if not exist ".venv" (
    echo Création de l'environnement virtuel...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
python -c "import torch" >nul 2>&1
if errorlevel 1 (
    echo Installation des dépendances...
    pip install -r requirements.txt
)
echo Démarrage du backend API...
start "MistralTune Backend" cmd /k "call .venv\Scripts\activate.bat && python src\api\main.py"
timeout /t 3 /nobreak >nul
echo Backend démarré: http://localhost:8000
echo Documentation API: http://localhost:8000/docs
if "%1"=="backend" goto end
goto start_frontend

:start_frontend
echo.
echo === Démarrage du Frontend ===
if not exist "frontend\node_modules" (
    echo Installation des dépendances frontend...
    cd frontend
    call npm install
    cd ..
)
echo Démarrage du frontend...
cd frontend
start "MistralTune Frontend" cmd /k "npm run dev"
cd ..
echo Frontend démarré: http://localhost:3000
if "%1"=="frontend" goto end
goto end

:start_train
echo.
echo === Lancement du Training (Demo) ===
if not exist "data\sample_train.jsonl" (
    echo Erreur: Fichier data\sample_train.jsonl non trouvé
    pause
    exit /b 1
)
if not exist "data\sample_eval.jsonl" (
    echo Erreur: Fichier data\sample_eval.jsonl non trouvé
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Création de l'environnement virtuel...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
python -c "import torch" >nul 2>&1
if errorlevel 1 (
    echo Installation des dépendances...
    pip install -r requirements.txt
)

echo.
echo Étape 1: Training...
python src\train_qlora.py --config configs\sample.yaml --lora configs\sample_lora.yaml --output_dir outputs\demo_run

if errorlevel 1 (
    echo Erreur: Training échoué
    pause
    exit /b 1
)

echo.
echo Étape 2: Évaluation...
python src\eval_em_f1.py --model_path outputs\demo_run --eval_file data\sample_eval.jsonl --is_adapter --save_results

if errorlevel 1 (
    echo Erreur: Évaluation échouée
    pause
    exit /b 1
)

echo.
echo === Training terminé avec succès! ===
echo Vérifiez outputs\demo_run pour l'adaptateur entraîné
echo Vérifiez reports\results.csv pour les métriques
goto end

:end
if "%1"=="all" (
    echo.
    echo === Services en cours d'exécution ===
    echo Backend: http://localhost:8000
    echo Frontend: http://localhost:3000
    echo.
    echo Les services tournent dans des fenêtres séparées.
    echo Fermez ces fenêtres pour arrêter les services.
)
echo.
pause
