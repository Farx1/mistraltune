#!/usr/bin/env python3
"""
Script de fine-tuning via l'API Mistral

Ce script permet de:
1. Préparer et uploader un dataset JSONL pour fine-tuning
2. Créer un job de fine-tuning avec hyperparamètres configurables
3. Suivre le statut du job jusqu'à la fin

Usage:
    python src/mistral_api_finetune.py --train_file data/train.jsonl --val_file data/val.jsonl

Exemple:
    python src/mistral_api_finetune.py \
        --train_file data/train.jsonl \
        --val_file data/val.jsonl \
        --model open-mistral-7b \
        --learning_rate 1e-4 \
        --epochs 3 \
        --suffix domain-qa
"""

import argparse
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from mistralai import Mistral


def validate_jsonl(file_path: str) -> tuple[bool, str, int]:
    """
    Valide un fichier JSONL et retourne les statistiques.
    
    Args:
        file_path: Chemin vers le fichier JSONL
        
    Returns:
        Tuple (is_valid, error_message, num_lines)
    """
    if not os.path.exists(file_path):
        return False, f"Fichier non trouvé: {file_path}", 0
    
    num_lines = 0
    required_fields = {"instruction", "output"}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    # Vérifier les champs requis
                    if not isinstance(data, dict):
                        return False, f"Ligne {line_num}: doit être un objet JSON", line_num
                    
                    missing_fields = required_fields - set(data.keys())
                    if missing_fields:
                        return False, f"Ligne {line_num}: champs manquants: {missing_fields}", line_num
                    
                    num_lines += 1
                except json.JSONDecodeError as e:
                    return False, f"Ligne {line_num}: JSON invalide - {str(e)}", line_num
        
        if num_lines == 0:
            return False, "Le fichier est vide ou ne contient que des lignes vides", 0
        
        return True, "", num_lines
    except Exception as e:
        return False, f"Erreur lors de la lecture: {str(e)}", num_lines


def upload_dataset(client: Mistral, file_path: str) -> str:
    """
    Upload un fichier JSONL vers l'API Mistral.
    
    Args:
        client: Client Mistral initialisé
        file_path: Chemin vers le fichier JSONL
        
    Returns:
        ID du fichier uploadé
    """
    print(f"Validation du fichier {file_path}...")
    is_valid, error_msg, num_lines = validate_jsonl(file_path)
    
    if not is_valid:
        raise ValueError(f"Fichier invalide: {error_msg}")
    
    print(f"✓ Fichier valide: {num_lines} exemples")
    print(f"Upload du fichier vers l'API Mistral...")
    
    with open(file_path, 'rb') as f:
        file_data = client.files.upload(
            file={
                "file_name": os.path.basename(file_path),
                "content": f,
            }
        )
    
    file_id = file_data.id
    print(f"✓ Fichier uploadé avec succès (ID: {file_id})")
    
    return file_id


def create_finetuning_job(
    client: Mistral,
    model: str,
    training_file_id: str,
    validation_file_id: Optional[str] = None,
    learning_rate: float = 1e-4,
    epochs: int = 3,
    batch_size: Optional[int] = None,
    suffix: Optional[str] = None,
    invalid_sample_skip_percentage: int = 0,
) -> Dict[str, Any]:
    """
    Crée un job de fine-tuning.
    
    Args:
        client: Client Mistral initialisé
        model: Modèle de base à fine-tuner (ex: "open-mistral-7b")
        training_file_id: ID du fichier d'entraînement uploadé
        validation_file_id: ID du fichier de validation (optionnel)
        learning_rate: Taux d'apprentissage
        epochs: Nombre d'époques
        batch_size: Taille du batch (optionnel, utilise la valeur par défaut si None)
        suffix: Suffixe pour le nom du modèle fine-tuné
        invalid_sample_skip_percentage: Pourcentage d'échantillons invalides à ignorer
        
    Returns:
        Dictionnaire avec les détails du job créé
    """
    print(f"\nCréation du job de fine-tuning...")
    print(f"  Modèle: {model}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Epochs: {epochs}")
    if batch_size:
        print(f"  Batch size: {batch_size}")
    if suffix:
        print(f"  Suffixe: {suffix}")
    
    hyperparameters = {
        "learning_rate": learning_rate,
    }
    
    job_params = {
        "model": model,
        "hyperparameters": hyperparameters,
        "training_file": training_file_id,
        "invalid_sample_skip_percentage": invalid_sample_skip_percentage,
    }
    
    if validation_file_id:
        job_params["validation_file"] = validation_file_id
        print(f"  Fichier de validation: {validation_file_id}")
    
    if suffix:
        job_params["suffix"] = suffix
    
    if epochs:
        job_params["epochs"] = epochs
    
    if batch_size:
        job_params["batch_size"] = batch_size
    
    job = client.fine_tuning.jobs.create(**job_params)
    
    print(f"✓ Job créé avec succès")
    print(f"  Job ID: {job.id}")
    print(f"  Statut: {job.status}")
    
    return {
        "id": job.id,
        "status": job.status,
        "model": job.model,
        "created_at": job.created_at,
        "fine_tuned_model": getattr(job, 'fine_tuned_model', None),
    }


def get_job_status(client: Mistral, job_id: str) -> Dict[str, Any]:
    """
    Récupère le statut d'un job de fine-tuning.
    
    Args:
        client: Client Mistral initialisé
        job_id: ID du job
        
    Returns:
        Dictionnaire avec le statut du job
    """
    job = client.fine_tuning.jobs.get(job_id=job_id)
    
    return {
        "id": job.id,
        "status": job.status,
        "model": job.model,
        "created_at": job.created_at,
        "fine_tuned_model": getattr(job, 'fine_tuned_model', None),
        "error": getattr(job, 'error', None),
    }


def wait_for_job_completion(
    client: Mistral,
    job_id: str,
    poll_interval: int = 30,
    max_wait_time: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Attend la fin d'un job de fine-tuning avec polling.
    
    Args:
        client: Client Mistral initialisé
        job_id: ID du job
        poll_interval: Intervalle de polling en secondes
        max_wait_time: Temps maximum d'attente en secondes (None = infini)
        
    Returns:
        Dictionnaire avec le statut final du job
    """
    print(f"\nSuivi du job {job_id}...")
    print("  (Appuyez sur Ctrl+C pour arrêter le suivi, le job continuera sur le serveur)")
    
    start_time = time.time()
    last_status = None
    
    try:
        while True:
            status_info = get_job_status(client, job_id)
            current_status = status_info["status"]
            
            # Afficher le statut seulement s'il a changé
            if current_status != last_status:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Statut: {current_status}")
                
                if status_info.get("fine_tuned_model"):
                    print(f"  Modèle fine-tuné: {status_info['fine_tuned_model']}")
                
                if status_info.get("error"):
                    print(f"  Erreur: {status_info['error']}")
                
                last_status = current_status
            
            # Vérifier si le job est terminé
            if current_status in ["succeeded", "failed", "cancelled"]:
                elapsed_time = time.time() - start_time
                print(f"\n✓ Job terminé après {elapsed_time/60:.1f} minutes")
                
                if current_status == "succeeded":
                    print(f"✓ Fine-tuning réussi!")
                    if status_info.get("fine_tuned_model"):
                        print(f"  Modèle disponible: {status_info['fine_tuned_model']}")
                elif current_status == "failed":
                    print(f"✗ Fine-tuning échoué")
                    if status_info.get("error"):
                        print(f"  Erreur: {status_info['error']}")
                else:
                    print(f"⚠ Job annulé")
                
                return status_info
            
            # Vérifier le temps maximum
            if max_wait_time and (time.time() - start_time) > max_wait_time:
                print(f"\n⚠ Temps maximum d'attente atteint ({max_wait_time/60:.1f} minutes)")
                print(f"  Le job continue sur le serveur. Utilisez --job_id {job_id} pour vérifier le statut plus tard.")
                return status_info
            
            # Attendre avant le prochain poll
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠ Suivi interrompu par l'utilisateur")
        print(f"  Le job continue sur le serveur. Utilisez --job_id {job_id} pour vérifier le statut plus tard.")
        return get_job_status(client, job_id)


def main():
    parser = argparse.ArgumentParser(
        description="Fine-tuning via l'API Mistral",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Fichiers
    parser.add_argument("--train_file", required=True, help="Chemin vers le fichier JSONL d'entraînement")
    parser.add_argument("--val_file", help="Chemin vers le fichier JSONL de validation (optionnel)")
    
    # Modèle et hyperparamètres
    parser.add_argument("--model", default="open-mistral-7b", help="Modèle de base (défaut: open-mistral-7b)")
    parser.add_argument("--learning_rate", type=float, default=1e-4, help="Taux d'apprentissage (défaut: 1e-4)")
    parser.add_argument("--epochs", type=int, default=3, help="Nombre d'époques (défaut: 3)")
    parser.add_argument("--batch_size", type=int, help="Taille du batch (optionnel)")
    parser.add_argument("--suffix", help="Suffixe pour le nom du modèle fine-tuné")
    
    # Options
    parser.add_argument("--job_id", help="ID d'un job existant à suivre (skip upload et création)")
    parser.add_argument("--poll_interval", type=int, default=30, help="Intervalle de polling en secondes (défaut: 30)")
    parser.add_argument("--max_wait_time", type=int, help="Temps maximum d'attente en secondes (optionnel)")
    parser.add_argument("--no_wait", action="store_true", help="Ne pas attendre la fin du job")
    
    args = parser.parse_args()
    
    # Vérifier la clé API
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY non définie. "
            "Définissez-la avec: export MISTRAL_API_KEY='votre-clé'"
        )
    
    # Initialiser le client
    client = Mistral(api_key=api_key)
    
    # Si un job_id est fourni, juste suivre ce job
    if args.job_id:
        print(f"Suivi du job existant: {args.job_id}")
        status_info = wait_for_job_completion(
            client,
            args.job_id,
            poll_interval=args.poll_interval,
            max_wait_time=args.max_wait_time,
        )
        return
    
    # Sinon, créer un nouveau job
    # Upload du fichier d'entraînement
    training_file_id = upload_dataset(client, args.train_file)
    
    # Upload du fichier de validation si fourni
    validation_file_id = None
    if args.val_file:
        validation_file_id = upload_dataset(client, args.val_file)
    
    # Créer le job
    job_info = create_finetuning_job(
        client=client,
        model=args.model,
        training_file_id=training_file_id,
        validation_file_id=validation_file_id,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        batch_size=args.batch_size,
        suffix=args.suffix,
    )
    
    # Suivre le job si demandé
    if not args.no_wait:
        wait_for_job_completion(
            client,
            job_info["id"],
            poll_interval=args.poll_interval,
            max_wait_time=args.max_wait_time,
        )
    else:
        print(f"\n✓ Job créé. Utilisez --job_id {job_info['id']} pour suivre le statut.")


if __name__ == "__main__":
    main()

