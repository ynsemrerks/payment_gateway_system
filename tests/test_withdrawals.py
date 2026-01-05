"""Tests for withdrawal endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.models.user import User


def test_create_withdrawal_success(client: TestClient, auth_headers: dict):
    """Test successful withdrawal creation."""
    response = client.post(
        "/api/v1/withdrawals",
        json={"amount": 50.00},
        headers={**auth_headers, "Idempotency-Key": "test-withdrawal-1"}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert data["type"] == "withdrawal"
    assert data["status"] == "pending"
    assert float(data["amount"]) == 50.00


def test_create_withdrawal_insufficient_balance(client: TestClient, auth_headers: dict, test_user: User):
    """Test withdrawal with insufficient balance."""
    # Try to withdraw more than balance
    response = client.post(
        "/api/v1/withdrawals",
        json={"amount": test_user.balance + 100},
        headers={**auth_headers, "Idempotency-Key": "test-insufficient"}
    )
    
    assert response.status_code == 400
    assert "insufficient_balance" in response.json()["detail"]["error"]


def test_create_withdrawal_idempotency(client: TestClient, auth_headers: dict):
    """Test idempotency key handling for withdrawals."""
    # First request
    response1 = client.post(
        "/api/v1/withdrawals",
        json={"amount": 50.00},
        headers={**auth_headers, "Idempotency-Key": "test-withdrawal-idempotency"}
    )
    assert response1.status_code == 202
    
    # Second request with same key
    response2 = client.post(
        "/api/v1/withdrawals",
        json={"amount": 100.00},  # Different amount
        headers={**auth_headers, "Idempotency-Key": "test-withdrawal-idempotency"}
    )
    assert response2.status_code == 202
    
    # Should return same response
    assert response1.json() == response2.json()


def test_get_withdrawal(client: TestClient, auth_headers: dict):
    """Test getting withdrawal details."""
    # Create withdrawal first
    create_response = client.post(
        "/api/v1/withdrawals",
        json={"amount": 50.00},
        headers={**auth_headers, "Idempotency-Key": "test-get-withdrawal"}
    )
    withdrawal_id = create_response.json()["id"]
    
    # Get withdrawal
    response = client.get(
        f"/api/v1/withdrawals/{withdrawal_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == withdrawal_id


def test_list_withdrawals(client: TestClient, auth_headers: dict):
    """Test listing withdrawals."""
    # Create a few withdrawals
    for i in range(2):
        client.post(
            "/api/v1/withdrawals",
            json={"amount": 10.00 + i},
            headers={**auth_headers, "Idempotency-Key": f"test-list-withdrawal-{i}"}
        )
    
    # List withdrawals
    response = client.get(
        "/api/v1/withdrawals",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 2
