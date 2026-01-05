"""Tests for deposit endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.models.user import User


def test_create_deposit_success(client: TestClient, auth_headers: dict):
    """Test successful deposit creation."""
    response = client.post(
        "/api/v1/deposits",
        json={"amount": 100.50},
        headers={**auth_headers, "Idempotency-Key": "test-deposit-1"}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert data["type"] == "deposit"
    assert data["status"] == "pending"
    assert float(data["amount"]) == 100.50


def test_create_deposit_idempotency(client: TestClient, auth_headers: dict):
    """Test idempotency key handling."""
    # First request
    response1 = client.post(
        "/api/v1/deposits",
        json={"amount": 100.00},
        headers={**auth_headers, "Idempotency-Key": "test-idempotency-1"}
    )
    assert response1.status_code == 202
    
    # Second request with same key
    response2 = client.post(
        "/api/v1/deposits",
        json={"amount": 200.00},  # Different amount
        headers={**auth_headers, "Idempotency-Key": "test-idempotency-1"}
    )
    assert response2.status_code == 202
    
    # Should return same response
    assert response1.json() == response2.json()


def test_create_deposit_missing_idempotency_key(client: TestClient, auth_headers: dict):
    """Test deposit creation without idempotency key."""
    response = client.post(
        "/api/v1/deposits",
        json={"amount": 100.00},
        headers=auth_headers
    )
    
    assert response.status_code == 400


def test_create_deposit_invalid_amount(client: TestClient, auth_headers: dict):
    """Test deposit with invalid amount."""
    response = client.post(
        "/api/v1/deposits",
        json={"amount": -50.00},
        headers={**auth_headers, "Idempotency-Key": "test-invalid-amount"}
    )
    
    assert response.status_code == 422


def test_get_deposit(client: TestClient, auth_headers: dict):
    """Test getting deposit details."""
    # Create deposit first
    create_response = client.post(
        "/api/v1/deposits",
        json={"amount": 100.00},
        headers={**auth_headers, "Idempotency-Key": "test-get-deposit"}
    )
    deposit_id = create_response.json()["id"]
    
    # Get deposit
    response = client.get(
        f"/api/v1/deposits/{deposit_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == deposit_id


def test_list_deposits(client: TestClient, auth_headers: dict):
    """Test listing deposits."""
    # Create a few deposits
    for i in range(3):
        client.post(
            "/api/v1/deposits",
            json={"amount": 100.00 + i},
            headers={**auth_headers, "Idempotency-Key": f"test-list-{i}"}
        )
    
    # List deposits
    response = client.get(
        "/api/v1/deposits",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3
