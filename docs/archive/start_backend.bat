@echo off
REM Script pour démarrer le backend FastAPI (Windows)

REM Activer l'environnement virtuel
call .venv\Scripts\activate.bat

REM Vérifier que la clé API est définie
if "%MISTRAL_API_KEY%"=="" (
    echo ⚠️  MISTRAL_API_KEY n'est pas définie
    echo Définissez-la avec: set MISTRAL_API_KEY=votre-clé
    exit /b 1
)

REM Démarrer le serveur
cd src\api
python main.py

