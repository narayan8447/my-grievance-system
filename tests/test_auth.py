import os
# Configure environment variables before importing app components
os.environ["SECRET_KEY"] = "super-secret-test-key-must-be-at-least-32-chars-long"

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.user import User, UserRegister, UserLogin, UserRole
from app.utils.security import (
    get_password_hash,
    verify_password,
    validate_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token
)
from app.services.auth_service import get_auth_service
from app.api.dependencies import (
    get_current_user,
    require_admin,
    require_citizen,
    require_addresser
)

# Mock implementation of database collection
class MockCollection:
    def __init__(self):
        self.data = {}

    async def find_one(self, query):
        for user_id, doc in self.data.items():
            if "user_id" in query and query["user_id"] == user_id:
                return doc
            if "email" in query and query["email"] == doc.get("email"):
                return doc
            if "phone" in query and query["phone"] == doc.get("phone"):
                return doc
            if "$or" in query:
                for clause in query["$or"]:
                    if "email" in clause and clause["email"] == doc.get("email"):
                        return doc
                    if "phone" in clause and clause["phone"] == doc.get("phone"):
                        return doc
        return None

    async def insert_one(self, doc):
        user_id = doc.get("user_id")
        self.data[user_id] = doc
        return doc

    async def update_one(self, query, update):
        doc = await self.find_one(query)
        if doc:
            if "$set" in update:
                doc.update(update["$set"])
        return doc


@pytest.fixture(autouse=True)
def mock_db():
    from app.models.database import db
    mock_users = MockCollection()
    
    def get_mock_collection(name):
        if name == "users":
            return mock_users
        return MagicMock()
        
    with patch.object(db, "get_collection", side_effect=get_mock_collection):
        yield mock_users


# =========================================================
# 1. Password Hashing and Validation Tests
# =========================================================

def test_password_validation():
    # Valid password
    is_valid, err = validate_password("SecurePass123")
    assert is_valid is True
    assert err is None

    # Invalid - Too short
    is_valid, err = validate_password("Short1")
    assert is_valid is False
    assert "at least 8 characters" in err

    # Invalid - No uppercase
    is_valid, err = validate_password("nocaps123")
    assert is_valid is False
    assert "at least one uppercase letter" in err

    # Invalid - No lowercase
    is_valid, err = validate_password("NOLOWERS123")
    assert is_valid is False
    assert "at least one lowercase letter" in err

    # Invalid - No digit
    is_valid, err = validate_password("NoDigitsHere")
    assert is_valid is False
    assert "at least one digit" in err


def test_password_hashing():
    password = "ValidPassword1"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword1", hashed) is False


# =========================================================
# 2. JWT Access and Refresh Token Tests
# =========================================================

def test_jwt_access_token_flow():
    data = {"sub": "USR-123", "role": "citizen"}
    token = create_access_token(data)
    
    # Successful decode
    payload = decode_access_token(token)
    assert payload["sub"] == "USR-123"
    assert payload["role"] == "citizen"
    assert "type" not in payload


def test_jwt_refresh_token_flow():
    data = {"sub": "USR-123", "role": "citizen"}
    token = create_refresh_token(data)
    
    # Successful decode
    payload = decode_refresh_token(token)
    assert payload["sub"] == "USR-123"
    assert payload["role"] == "citizen"
    assert payload["type"] == "refresh"


def test_jwt_type_cross_validation_prevention():
    data = {"sub": "USR-123"}
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)

    # Access token decoding should reject refresh token
    with pytest.raises(HTTPException) as excinfo:
        decode_access_token(refresh_token)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Access token required" in excinfo.value.detail

    # Refresh token decoding should reject access token
    with pytest.raises(HTTPException) as excinfo:
        decode_refresh_token(access_token)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Refresh token required" in excinfo.value.detail


# =========================================================
# 3. Role Authorization & Route Protection Tests
# =========================================================

@pytest.mark.asyncio
async def test_role_authorization_dependencies():
    # 1. Test Citizen Dependency
    citizen_user = User(
        user_id="USR-CIT-123",
        email="citizen@test.com",
        password_hash="...",
        full_name="Citizen User",
        role="citizen",
        created_at=datetime.utcnow()
    )
    assert await require_citizen(citizen_user) == citizen_user
    
    with pytest.raises(HTTPException) as excinfo:
        await require_admin(citizen_user)
    assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN

    # 2. Test Admin Dependency
    admin_user = User(
        user_id="USR-ADM-123",
        email="admin@test.com",
        password_hash="...",
        full_name="Admin User",
        role="admin",
        created_at=datetime.utcnow()
    )
    assert await require_admin(admin_user) == admin_user

    with pytest.raises(HTTPException) as excinfo:
        await require_citizen(admin_user)
    assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN

    # 3. Test Addresser Dependency
    addresser_user = User(
        user_id="USR-ADD-123",
        email="addresser@test.com",
        password_hash="...",
        full_name="Addresser User",
        role="addresser",
        department="Municipal",
        created_at=datetime.utcnow()
    )
    assert await require_addresser(addresser_user) == addresser_user

    # Addresser must have a department
    addresser_no_dept = User(
        user_id="USR-ADD-124",
        email="addresser2@test.com",
        password_hash="...",
        full_name="Addresser No Dept",
        role="addresser",
        department=None,
        created_at=datetime.utcnow()
    )
    with pytest.raises(HTTPException) as excinfo:
        await require_addresser(addresser_no_dept)
    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST


# =========================================================
# 4. API Endpoint Integration Tests (Register, Login, Refresh)
# =========================================================

def test_api_auth_endpoints(mock_db):
    client = TestClient(app)
    
    # 1. Register a user
    register_data = {
        "email": "newuser@test.com",
        "phone": "+919876543210",
        "password": "Password123",
        "full_name": "New User",
        "role": "citizen"
    }
    
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == status.HTTP_201_CREATED
    res_data = response.json()
    assert "access_token" in res_data
    assert "refresh_token" in res_data
    assert res_data["user"]["email"] == "newuser@test.com"
    
    refresh_token = res_data["refresh_token"]

    # 2. Login the user
    login_data = {
        "email_or_phone": "newuser@test.com",
        "password": "Password123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    res_data = response.json()
    assert "access_token" in res_data
    assert "refresh_token" in res_data
    
    # 3. Refresh token
    refresh_payload = {
        "refresh_token": refresh_token
    }
    response = client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == status.HTTP_200_OK
    res_data = response.json()
    assert "access_token" in res_data
    assert "refresh_token" in res_data

    # 4. Refresh token with invalid/access token
    invalid_refresh_payload = {
        "refresh_token": res_data["access_token"]
    }
    response = client.post("/api/v1/auth/refresh", json=invalid_refresh_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
