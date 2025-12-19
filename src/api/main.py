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
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from mistralai import Mistral
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
# Look for .env in project root (two levels up from this file)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mistral_api_finetune import upload_dataset, create_finetuning_job, get_job_status, validate_jsonl
from mistral_api_inference import compare_responses, generate_response
from db.database import init_db, get_db
from db.models import Job, Dataset, DatasetVersion
from jobs.state_machine import JobState, update_job_status
from jobs.logging import get_job_logs
from storage.s3_client import get_storage_client
from datasets.versioning import create_dataset_version, compute_dataset_hash

# Import custom logging (avoid conflict with stdlib logging)
import importlib.util
logging_config_path = Path(__file__).parent.parent / "logging" / "config.py"
spec = importlib.util.spec_from_file_location("app_logging_config", logging_config_path)
app_logging_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_logging_config)

logging_middleware_path = Path(__file__).parent.parent / "logging" / "middleware.py"
spec_mw = importlib.util.spec_from_file_location("app_logging_middleware", logging_middleware_path)
app_logging_middleware = importlib.util.module_from_spec(spec_mw)
spec_mw.loader.exec_module(app_logging_middleware)

from metrics.collector import get_metrics_collector


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


# Database initialization - now using SQLAlchemy ORM


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

# Setup logging
app_logging_config.setup_logging()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(app_logging_middleware.CorrelationIDMiddleware)

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
async def health(db: Session = Depends(get_db)):
    """Endpoint de santé avec vérification des dépendances."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "mistral_api_configured": bool(os.getenv("MISTRAL_API_KEY")),
    }
    
    # Check database connectivity
    try:
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity (if configured)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    # Check S3 connectivity (if configured)
    storage_client = get_storage_client()
    if storage_client.config.use_s3:
        try:
            # Try to list buckets
            if storage_client.s3_client:
                storage_client.s3_client.list_buckets()
                health_status["storage"] = "connected"
            else:
                health_status["storage"] = "local_fallback"
        except Exception as e:
            health_status["storage"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["storage"] = "local_filesystem"
    
    return health_status


@app.get("/api/metrics")
async def get_metrics():
    """Expose metrics in Prometheus-style format."""
    metrics_collector = get_metrics_collector()
    metrics = metrics_collector.get_metrics()
    
    # Format as Prometheus-style text (simple version)
    lines = []
    lines.append("# HELP mistraltune_active_jobs Number of active jobs")
    lines.append(f"mistraltune_active_jobs {metrics['jobs']['active']}")
    
    for job_type, duration in metrics["jobs"]["durations"].items():
        lines.append(f"# HELP mistraltune_job_duration_seconds Job duration in seconds")
        lines.append(f'mistraltune_job_duration_seconds{{job_type="{job_type}"}} {duration}')
    
    for key, count in metrics["jobs"]["counts"].items():
        parts = key.split("_")
        job_type = parts[0]
        status = "_".join(parts[1:])
        lines.append(f'# HELP mistraltune_job_count Total number of jobs')
        lines.append(f'mistraltune_job_count{{job_type="{job_type}",status="{status}"}} {count}')
    
    lines.append(f"# HELP mistraltune_api_latency_p50 API latency p50 in milliseconds")
    lines.append(f"mistraltune_api_latency_p50 {metrics['api']['latency_ms']['p50']}")
    
    return Response(content="\n".join(lines), media_type="text/plain")


# Datasets endpoints
@app.post("/api/datasets/upload")
@app.post("/datasets/upload")  # Frontend compatibility
async def upload_dataset_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
        uploaded_at = int(datetime.now().timestamp())
        
        # Compute file hash
        file_hash = compute_dataset_hash(temp_path)
        
        # Upload to storage (S3 or local)
        storage_client = get_storage_client()
        storage_key = f"{file_id}/{file.filename}"
        s3_key = storage_client.upload_file(temp_path, storage_key, bucket_type="datasets")
        
        # Sauvegarder dans la DB avec ORM
        dataset = Dataset(
            id=file_id,
            filename=file.filename,
            file_hash=file_hash,
            size_bytes=len(content),
            uploaded_at=uploaded_at,
            metadata_json={"size": len(content), "num_samples": num_lines},
        )
        db.add(dataset)
        
        # Create initial version with storage
        version = create_dataset_version(db, file_id, temp_path, s3_key=s3_key)
        
        # Nettoyer le fichier temporaire
        temp_path.unlink()
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "num_samples": num_lines,
            "status": "uploaded"
        }
    except Exception as e:
        db.rollback()
        temp_path.unlink()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")


@app.get("/api/datasets")
@app.get("/datasets")  # Frontend compatibility
async def list_datasets(db: Session = Depends(get_db)):
    """Liste tous les datasets uploadés."""
    datasets_query = db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
    datasets = [d.to_dict() for d in datasets_query]
    return {"datasets": datasets}


# Jobs endpoints
@app.post("/api/jobs")
@app.post("/jobs")  # Frontend compatibility
async def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Crée un nouveau job de fine-tuning.
    
    Supporte:
    - API Mistral (job_type="mistral_api")
    - QLoRA local (job_type="qlora_local") - à implémenter
    """
    if request.job_type == "mistral_api":
        # Check if Celery is available (Redis configured)
        use_celery = bool(os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL"))
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
            
            # Sauvegarder dans la DB avec ORM
            job = Job(
                id=job_info["id"],
                job_type="mistral_api",
                model=request.model,
                status=JobState.PENDING.value,  # Start as PENDING, will be queued
                created_at=job_info["created_at"],
                started_at=None,
                finished_at=None,
                progress=None,
                error_message=None,
                config_json={
                    "learning_rate": request.learning_rate,
                    "epochs": request.epochs,
                    "batch_size": request.batch_size,
                    "suffix": request.suffix,
                },
                dataset_version_id=None,  # Will be linked in Phase C
                model_output_ref=None,
                metrics_json={"training_file_id": request.training_file_id},
            )
            db.add(job)
            db.commit()
            
            # Enqueue Celery task if available, otherwise use BackgroundTasks (fallback)
            if use_celery:
                try:
                    from workers.tasks import execute_mistral_api_job
                    # Update status to QUEUED
                    update_job_status(db, job_info["id"], JobState.QUEUED.value)
                    # Enqueue task
                    execute_mistral_api_job.delay(job_info["id"])
                except Exception as e:
                    # Fallback to BackgroundTasks if Celery fails
                    logger.warning(f"Celery not available, using BackgroundTasks: {e}")
                    use_celery = False
            
            if not use_celery:
                # Fallback: Use BackgroundTasks (original behavior)
                # This maintains backward compatibility
                from api.main import _poll_job_status_background
                background_tasks.add_task(_poll_job_status_background, job_info["id"])
            
            return {
                "id": job_info["id"],
                "job_id": job_info["id"],  # For backward compatibility
                "status": job.status,
                "message": "Job créé avec succès"
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Erreur lors de la création du job: {str(e)}")
    
    elif request.job_type == "qlora_local":
        # TODO: Implémenter la création de job QLoRA local
        raise HTTPException(
            status_code=501,
            detail="QLoRA local non encore implémenté dans l'API"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Type de job invalide: {request.job_type}")


@app.post("/api/jobs/create")
async def create_job_legacy(request: JobCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Legacy endpoint for backward compatibility."""
    result = await create_job(request, background_tasks, db)
    return result


@app.get("/api/jobs")
@app.get("/jobs")  # Frontend compatibility
async def list_jobs(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Liste tous les jobs avec filtres optionnels."""
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    jobs_query = query.order_by(Job.created_at.desc()).all()
    jobs = [j.to_dict() for j in jobs_query]
    return {"jobs": jobs}


@app.get("/api/jobs/{job_id}")
@app.get("/jobs/{job_id}")  # Frontend compatibility
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Récupère un job par son ID (frontend endpoint)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    # Si c'est un job Mistral API, récupérer le statut à jour
    if job.job_type == 'mistral_api':
        try:
            client = get_mistral_client()
            status_info = get_job_status(client, job_id)
            
            # Map Mistral status (lowercase) to our status format
            mistral_status = status_info["status"].lower()
            status_map = {
                "validated": "QUEUED",
                "queued": "QUEUED",
                "running": "RUNNING",
                "succeeded": "SUCCEEDED",
                "failed": "FAILED",
                "cancelled": "CANCELLED",
            }
            mapped_status = status_map.get(mistral_status, mistral_status.upper())
            
            # Mettre à jour la DB avec ORM
            job.status = mapped_status
            job.model_output_ref = status_info.get("fine_tuned_model")
            if status_info.get("error"):
                job.error_message = str(status_info.get("error"))
            db.commit()
            
            # Return in format expected by frontend
            job_dict = job.to_dict()
            return {"job": job_dict}
        except Exception as e:
            # Retourner le statut de la DB en cas d'erreur
            job_dict = job.to_dict()
            return {"job": job_dict}
    else:
        job_dict = job.to_dict()
        return {"job": job_dict}


@app.get("/api/jobs/{job_id}/status")
async def get_job_status_endpoint(job_id: str, db: Session = Depends(get_db)):
    """Récupère le statut d'un job (legacy endpoint)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    # Si c'est un job Mistral API, récupérer le statut à jour
    if job.job_type == 'mistral_api':
        try:
            client = get_mistral_client()
            status_info = get_job_status(client, job_id)
            
            # Map Mistral status (lowercase) to our status format
            mistral_status = status_info["status"].lower()
            status_map = {
                "validated": "QUEUED",
                "queued": "QUEUED",
                "running": "RUNNING",
                "succeeded": "SUCCEEDED",
                "failed": "FAILED",
                "cancelled": "CANCELLED",
            }
            mapped_status = status_map.get(mistral_status, mistral_status.upper())
            
            # Mettre à jour la DB avec ORM
            job.status = mapped_status
            job.model_output_ref = status_info.get("fine_tuned_model")
            if status_info.get("error"):
                job.error_message = str(status_info.get("error"))
            db.commit()
            
            return JobStatusResponse(
                id=job.id,
                status=mapped_status,
                model=job.model,
                created_at=job.created_at,
                fine_tuned_model=job.model_output_ref,
                error=job.error_message,
                progress=job.progress,
            )
        except Exception as e:
            # Retourner le statut de la DB en cas d'erreur
            return JobStatusResponse(
                id=job.id,
                status=job.status,
                model=job.model,
                created_at=job.created_at,
                fine_tuned_model=job.model_output_ref,
                error=job.error_message,
                progress=job.progress,
            )
    else:
        return JobStatusResponse(
            id=job.id,
            status=job.status,
            model=job.model,
            created_at=job.created_at,
            fine_tuned_model=job.model_output_ref,
            error=job.error_message,
            progress=job.progress,
        )


@app.websocket("/api/jobs/{job_id}/ws")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket pour le monitoring temps réel d'un job.
    
    Envoie des mises à jour de statut et logs en temps réel.
    Reads from Redis pub/sub for logs and polls DB for status.
    """
    await manager.connect(websocket, job_id)
    
    # Get database session for this connection
    from db.database import SessionLocal
    db = SessionLocal()
    
    # Try to subscribe to Redis pub/sub for logs
    redis_sub = None
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_sub = redis_client.pubsub()
        redis_sub.subscribe(f"job_logs:{job_id}")
    except Exception as e:
        logger.debug(f"Redis not available for log streaming: {e}")
    
    try:
        while True:
            # Check for new logs from Redis pub/sub
            if redis_sub:
                try:
                    message = redis_sub.get_message(timeout=0.1)
                    if message and message["type"] == "message":
                        log_data = json.loads(message["data"])
                        await manager.send_personal_message({
                            "type": "log",
                            "job_id": job_id,
                            "timestamp": log_data["timestamp"],
                            "level": log_data["level"],
                            "message": log_data["message"],
                        }, job_id)
                except Exception as e:
                    logger.debug(f"Error reading Redis message: {e}")
            
            # Récupérer le statut
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                
                if job:
                    # Si c'est un job Mistral, récupérer le statut à jour
                    if job.job_type == 'mistral_api':
                        client = get_mistral_client()
                        status_info = get_job_status(client, job_id)
                        
                        # Map Mistral status (lowercase) to our status format
                        mistral_status = status_info["status"].lower()
                        # Mistral uses: validated, queued, running, succeeded, failed, cancelled
                        # Our states are: PENDING, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED
                        status_map = {
                            "validated": "QUEUED",
                            "queued": "QUEUED",
                            "running": "RUNNING",
                            "succeeded": "SUCCEEDED",
                            "failed": "FAILED",
                            "cancelled": "CANCELLED",
                        }
                        mapped_status = status_map.get(mistral_status, mistral_status.upper())
                        
                        # Mettre à jour la DB avec ORM
                        job.status = mapped_status
                        job.model_output_ref = status_info.get("fine_tuned_model")
                        if status_info.get("error"):
                            job.error_message = str(status_info.get("error"))
                        db.commit()
                        
                        await manager.send_personal_message({
                            "type": "status_update",
                            "job_id": job_id,
                            "status": mapped_status,
                            "fine_tuned_model": status_info.get("fine_tuned_model"),
                            "error": status_info.get("error"),
                            "timestamp": datetime.now().isoformat(),
                        }, job_id)
                        
                        # Si terminé, arrêter le polling
                        if mapped_status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                            break
                    else:
                        await manager.send_personal_message({
                            "type": "status_update",
                            "job_id": job_id,
                            "status": job.status,
                            "timestamp": datetime.now().isoformat(),
                        }, job_id)
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "message": str(e),
                }, job_id)
            
            await asyncio.sleep(5)  # Poll toutes les 5 secondes
            
    except WebSocketDisconnect:
        manager.disconnect(job_id)
    finally:
        if redis_sub:
            redis_sub.unsubscribe(f"job_logs:{job_id}")
            redis_sub.close()
        db.close()


@app.post("/api/jobs/{job_id}/cancel")
@app.post("/jobs/{job_id}/cancel")  # Frontend compatibility
async def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Annule un job en cours."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    # Vérifier si le job peut être annulé
    if job.status in ["succeeded", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Le job est déjà {job.status}")
    
    # Marquer comme annulé
    job.status = "cancelled"
    job.finished_at = int(datetime.now().timestamp())
    db.commit()
    
    # Revoke Celery task if running
    use_celery = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL")
    if use_celery:
        try:
            from workers.celery_app import celery_app
            celery_app.control.revoke(job_id, terminate=True)
        except Exception as e:
            logger.warning(f"Failed to revoke Celery task: {e}")
    
    return {"message": "Job annulé", "job_id": job_id, "status": "cancelled"}


@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs_endpoint(
    job_id: str,
    limit: int = 100,
    offset: int = 0,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Récupère les logs d'un job avec pagination."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    logs = get_job_logs(db, job_id, limit=limit, offset=offset, level=level)
    return {"logs": logs, "total": len(logs)}


# Background task fallback (for when Celery is not available)
async def _poll_job_status_background(job_id: str):
    """Background task to poll job status (fallback when Celery unavailable)."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        if job.job_type == "mistral_api":
            client = get_mistral_client()
            status_info = get_job_status(client, job_id)
            job.status = status_info["status"]
            job.model_output_ref = status_info.get("fine_tuned_model")
            if status_info.get("error"):
                job.error_message = str(status_info.get("error"))
            db.commit()
    finally:
        db.close()


# Authentication endpoints
@app.post("/api/auth/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db),
):
    """Login endpoint to get JWT token."""
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() in ("true", "1", "yes")
    if not auth_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled",
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }


@app.post("/api/auth/register")
async def register(
    email: str,
    password: str,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    auth_required = os.getenv("AUTH_REQUIRED", "false").lower() in ("true", "1", "yes")
    if not auth_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled",
        )
    
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    import time
    user = User(
        id=f"user_{int(time.time())}_{email[:8]}",
        email=email,
        password_hash=hash_password(password),
        role="member",
        created_at=int(time.time()),
    )
    db.add(user)
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }


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

