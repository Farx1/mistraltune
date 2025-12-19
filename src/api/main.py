"""
Backend FastAPI pour MistralTune

Fournit des endpoints REST et WebSocket pour:
- Upload et validation de datasets
- Création et suivi de jobs de fine-tuning (API Mistral et QLoRA local)
- Inférence et comparaison de modèles
- Monitoring temps réel via WebSocket
"""

import os
import json
import asyncio
import sqlite3
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from mistralai import Mistral

# Load environment variables from .env file
# Look for .env in project root (two levels up from this file)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mistral_api_finetune import upload_dataset, create_finetuning_job, get_job_status, validate_jsonl
from mistral_api_inference import compare_responses, generate_response


# Modèles Pydantic
class JobCreateRequest(BaseModel):
    model: str = Field(default="open-mistral-7b", description="Modèle de base")
    training_file_id: str = Field(description="ID du fichier d'entraînement")
    validation_file_id: Optional[str] = Field(None, description="ID du fichier de validation")
    learning_rate: float = Field(default=1e-4, description="Taux d'apprentissage")
    epochs: int = Field(default=3, description="Nombre d'époques")
    batch_size: Optional[int] = Field(None, description="Taille du batch")
    suffix: Optional[str] = Field(None, description="Suffixe pour le modèle")
    job_type: str = Field(default="mistral_api", description="Type de job: mistral_api ou qlora_local")


class InferenceRequest(BaseModel):
    base_model: str = Field(description="Modèle de base")
    fine_tuned_model: str = Field(description="Modèle fine-tuné")
    prompts: List[str] = Field(description="Liste de prompts à tester")
    temperature: float = Field(default=0.7, description="Température")
    max_tokens: int = Field(default=512, description="Nombre max de tokens")


class JobStatusResponse(BaseModel):
    id: str
    status: str
    model: str
    created_at: int
    fine_tuned_model: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[float] = None


# Base de données SQLite pour l'historique
DB_PATH = Path("data/jobs.db")


def init_db():
    """Initialise la base de données SQLite."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            job_type TEXT NOT NULL,
            model TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            fine_tuned_model TEXT,
            error TEXT,
            config TEXT,
            metadata TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_id TEXT,
            num_samples INTEGER,
            uploaded_at INTEGER NOT NULL,
            metadata TEXT
        )
    """)
    
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    init_db()
    yield


# Initialiser l'application
app = FastAPI(
    title="MistralTune API",
    description="API pour le fine-tuning de modèles Mistral",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Client Mistral global
mistral_client: Optional[Mistral] = None


def _create_mock_client():
    """Create a mock Mistral client for demo mode."""
    from unittest.mock import Mock
    mock_client = Mock()
    # Mock files.upload
    mock_upload = Mock()
    mock_upload.id = "file_demo123"
    mock_upload.filename = "demo.jsonl"
    mock_upload.purpose = "fine-tuning"
    mock_client.files = Mock()
    mock_client.files.upload = Mock(return_value=mock_upload)
    # Mock fine_tuning.jobs
    mock_job = Mock()
    mock_job.id = "ftjob_demo123"
    mock_job.model = "open-mistral-7b"
    mock_job.status = "validated"
    mock_job.created_at = 1234567890
    mock_job.fine_tuned_model = None
    mock_job.error = None
    mock_client.fine_tuning = Mock()
    mock_client.fine_tuning.jobs = Mock()
    mock_client.fine_tuning.jobs.create = Mock(return_value=mock_job)
    # Mock job status
    mock_job_status = Mock()
    mock_job_status.id = "ftjob_demo123"
    mock_job_status.model = "open-mistral-7b"
    mock_job_status.status = "succeeded"
    mock_job_status.created_at = 1234567890
    mock_job_status.fine_tuned_model = "ft:open-mistral-7b:demo123:20240101:abc123"
    mock_job_status.error = None
    mock_client.fine_tuning.jobs.get = Mock(return_value=mock_job_status)
    # Mock chat completions
    mock_chat_response = Mock()
    mock_choice = Mock()
    mock_choice.message = Mock()
    mock_choice.message.content = "Demo response from fine-tuned model."
    mock_choice.finish_reason = "stop"
    mock_chat_response.choices = [mock_choice]
    mock_chat_response.usage = Mock()
    mock_chat_response.usage.prompt_tokens = 10
    mock_chat_response.usage.completion_tokens = 20
    mock_chat_response.usage.total_tokens = 30
    mock_client.chat = Mock()
    mock_client.chat.completions = Mock()
    mock_client.chat.completions.create = Mock(return_value=mock_chat_response)
    return mock_client


def get_mistral_client() -> Mistral:
    """
    Récupère ou crée le client Mistral.
    
    En mode DEMO (DEMO_MODE=1), retourne un mock client pour les tests.
    """
    global mistral_client
    
    # Check for demo mode
    demo_mode = os.getenv("DEMO_MODE", "0").lower() in ("1", "true", "yes")
    
    if mistral_client is None:
        if demo_mode:
            # Return a mock client for testing
            mistral_client = _create_mock_client()
        else:
            # Normal mode - use real API
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                # If no key and not in demo mode, show warning and use mock
                import warnings
                warnings.warn(
                    "MISTRAL_API_KEY not set. Some features will be disabled. "
                    "Set DEMO_MODE=1 for testing.",
                    UserWarning
                )
                mistral_client = _create_mock_client()
            else:
                mistral_client = Mistral(api_key=api_key)
    
    return mistral_client


# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id] = websocket
    
    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
    
    async def send_personal_message(self, message: dict, job_id: str):
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(message)
            except:
                self.disconnect(job_id)


manager = ConnectionManager()


# Endpoints
@app.get("/")
async def root():
    return {
        "message": "MistralTune API",
        "version": "1.0.0",
        "endpoints": {
            "datasets": "/api/datasets",
            "jobs": "/api/jobs",
            "inference": "/api/inference",
        }
    }


@app.get("/api/health")
async def health():
    """Endpoint de santé."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "mistral_api_configured": bool(os.getenv("MISTRAL_API_KEY"))
    }


# Datasets endpoints
@app.post("/api/datasets/upload")
async def upload_dataset_endpoint(file: UploadFile = File(...)):
    """
    Upload et validation d'un fichier JSONL.
    
    Returns:
        ID du fichier uploadé et statistiques
    """
    if not file.filename.endswith('.jsonl'):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format .jsonl")
    
    # Sauvegarder temporairement
    temp_path = Path(f"data/uploads/{file.filename}")
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = await file.read()
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    # Valider le fichier
    is_valid, error_msg, num_lines = validate_jsonl(str(temp_path))
    
    if not is_valid:
        temp_path.unlink()
        raise HTTPException(status_code=400, detail=f"Fichier invalide: {error_msg}")
    
    # Upload vers Mistral
    try:
        client = get_mistral_client()
        with open(temp_path, 'rb') as f:
            file_data = client.files.upload(
                file={
                    "file_name": file.filename,
                    "content": f,
                }
            )
        
        file_id = file_data.id
        
        # Sauvegarder dans la DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO datasets (id, filename, file_id, num_samples, uploaded_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            file.filename,
            file_id,
            num_lines,
            int(datetime.now().timestamp()),
            json.dumps({"size": len(content)})
        ))
        conn.commit()
        conn.close()
        
        # Nettoyer le fichier temporaire
        temp_path.unlink()
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "num_samples": num_lines,
            "status": "uploaded"
        }
    except Exception as e:
        temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")


@app.get("/api/datasets")
async def list_datasets():
    """Liste tous les datasets uploadés."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets ORDER BY uploaded_at DESC")
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    datasets = []
    for row in rows:
        dataset = dict(zip(columns, row))
        if dataset.get('metadata'):
            dataset['metadata'] = json.loads(dataset['metadata'])
        datasets.append(dataset)
    
    conn.close()
    return {"datasets": datasets}


# Jobs endpoints
@app.post("/api/jobs/create")
async def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks):
    """
    Crée un nouveau job de fine-tuning.
    
    Supporte:
    - API Mistral (job_type="mistral_api")
    - QLoRA local (job_type="qlora_local") - à implémenter
    """
    if request.job_type == "mistral_api":
        try:
            client = get_mistral_client()
            
            job_info = create_finetuning_job(
                client=client,
                model=request.model,
                training_file_id=request.training_file_id,
                validation_file_id=request.validation_file_id,
                learning_rate=request.learning_rate,
                epochs=request.epochs,
                batch_size=request.batch_size,
                suffix=request.suffix,
            )
            
            # Sauvegarder dans la DB
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jobs (id, job_type, model, status, created_at, updated_at, config, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_info["id"],
                "mistral_api",
                request.model,
                job_info["status"],
                job_info["created_at"],
                int(datetime.now().timestamp()),
                json.dumps({
                    "learning_rate": request.learning_rate,
                    "epochs": request.epochs,
                    "batch_size": request.batch_size,
                    "suffix": request.suffix,
                }),
                json.dumps({"training_file_id": request.training_file_id})
            ))
            conn.commit()
            conn.close()
            
            return {
                "job_id": job_info["id"],
                "status": job_info["status"],
                "message": "Job créé avec succès"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la création du job: {str(e)}")
    
    elif request.job_type == "qlora_local":
        # TODO: Implémenter la création de job QLoRA local
        raise HTTPException(
            status_code=501,
            detail="QLoRA local non encore implémenté dans l'API"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Type de job invalide: {request.job_type}")


@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    """Liste tous les jobs avec filtres optionnels."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if status:
        cursor.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    else:
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    jobs = []
    for row in rows:
        job = dict(zip(columns, row))
        if job.get('config'):
            job['config'] = json.loads(job['config'])
        if job.get('metadata'):
            job['metadata'] = json.loads(job['metadata'])
        jobs.append(job)
    
    conn.close()
    return {"jobs": jobs}


@app.get("/api/jobs/{job_id}/status")
async def get_job_status_endpoint(job_id: str):
    """Récupère le statut d'un job."""
    # Récupérer depuis la DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    columns = [desc[0] for desc in cursor.description]
    job_db = dict(zip(columns, row))
    conn.close()
    
    # Si c'est un job Mistral API, récupérer le statut à jour
    if job_db.get('job_type') == 'mistral_api':
        try:
            client = get_mistral_client()
            status_info = get_job_status(client, job_id)
            
            # Mettre à jour la DB
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE jobs 
                SET status = ?, fine_tuned_model = ?, error = ?, updated_at = ?
                WHERE id = ?
            """, (
                status_info["status"],
                status_info.get("fine_tuned_model"),
                json.dumps(status_info.get("error")) if status_info.get("error") else None,
                int(datetime.now().timestamp()),
                job_id
            ))
            conn.commit()
            conn.close()
            
            return JobStatusResponse(**status_info)
        except Exception as e:
            # Retourner le statut de la DB en cas d'erreur
            return JobStatusResponse(
                id=job_db['id'],
                status=job_db['status'],
                model=job_db['model'],
                created_at=job_db['created_at'],
                fine_tuned_model=job_db.get('fine_tuned_model'),
                error=job_db.get('error'),
            )
    else:
        return JobStatusResponse(
            id=job_db['id'],
            status=job_db['status'],
            model=job_db['model'],
            created_at=job_db['created_at'],
            fine_tuned_model=job_db.get('fine_tuned_model'),
            error=job_db.get('error'),
        )


@app.websocket("/api/jobs/{job_id}/ws")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket pour le monitoring temps réel d'un job.
    
    Envoie des mises à jour de statut toutes les 5 secondes.
    """
    await manager.connect(websocket, job_id)
    
    try:
        while True:
            # Récupérer le statut
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    job = dict(zip(columns, row))
                    
                    # Si c'est un job Mistral, récupérer le statut à jour
                    if job.get('job_type') == 'mistral_api':
                        client = get_mistral_client()
                        status_info = get_job_status(client, job_id)
                        
                        await manager.send_personal_message({
                            "type": "status_update",
                            "job_id": job_id,
                            "status": status_info["status"],
                            "fine_tuned_model": status_info.get("fine_tuned_model"),
                            "error": status_info.get("error"),
                            "timestamp": datetime.now().isoformat(),
                        }, job_id)
                        
                        # Si terminé, arrêter le polling
                        if status_info["status"] in ["succeeded", "failed", "cancelled"]:
                            break
                    else:
                        await manager.send_personal_message({
                            "type": "status_update",
                            "job_id": job_id,
                            "status": job['status'],
                            "timestamp": datetime.now().isoformat(),
                        }, job_id)
                
                conn.close()
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "message": str(e),
                }, job_id)
            
            await asyncio.sleep(5)  # Poll toutes les 5 secondes
            
    except WebSocketDisconnect:
        manager.disconnect(job_id)


# Inference endpoints
@app.post("/api/inference/compare")
async def compare_models(request: InferenceRequest):
    """
    Compare les réponses de deux modèles sur une liste de prompts.
    """
    try:
        client = get_mistral_client()
        
        results = compare_responses(
            client,
            request.base_model,
            request.fine_tuned_model,
            request.prompts,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")


@app.post("/api/inference/generate")
async def generate_inference(
    model: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 512,
):
    """
    Génère une réponse avec un modèle.
    """
    try:
        client = get_mistral_client()
        response = generate_response(
            client,
            model,
            prompt,
            temperature,
            max_tokens,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

