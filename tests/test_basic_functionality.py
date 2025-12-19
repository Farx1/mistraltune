"""
Tests basiques pour vérifier que l'application fonctionne.
"""

import pytest
from fastapi import status


def test_health_check(client):
    """Test que l'endpoint de santé fonctionne."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data


def test_root_endpoint(client):
    """Test que l'endpoint racine fonctionne."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_list_jobs_empty(client):
    """Test que lister les jobs fonctionne même quand il n'y en a pas."""
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_list_datasets_empty(client):
    """Test que lister les datasets fonctionne même quand il n'y en a pas."""
    response = client.get("/api/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "datasets" in data
    assert isinstance(data["datasets"], list)


def test_get_nonexistent_job(client):
    """Test que récupérer un job inexistant retourne 404."""
    response = client.get("/api/jobs/nonexistent_job_id")
    assert response.status_code == 404


def test_cancel_nonexistent_job(client):
    """Test que annuler un job inexistant retourne 404."""
    response = client.post("/api/jobs/nonexistent_job_id/cancel")
    assert response.status_code == 404


def test_metrics_endpoint(client):
    """Test que l'endpoint de métriques fonctionne."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    # Devrait retourner du texte Prometheus
    assert "mistraltune" in response.text

