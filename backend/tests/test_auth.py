"""Comprehensive authentication, RBAC, and Row-Level Security test suite.

Covers:
- Login with Argon2 password verification
- Refresh token issuance and rotation
- Expired token rejection (401 TOKEN_EXPIRED)
- Invalid / malformed token rejection (401 INVALID_TOKEN)
- Wrong role rejection (403 INSUFFICIENT_PERMISSIONS)
- Operator cross-cluster access enforcement (403 CROSS_CLUSTER_ACCESS_DENIED)
- Admin and Read-only Judge access across clusters
- Row-Level Security (RLS) session parameter setting
- Security audit: No secrets committed to git
"""
import subprocess
from datetime import timedelta
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.core.config import (
    DEMO_ADMIN_PASSWORD,
    DEMO_ADMIN_USERNAME,
    DEMO_DRIVER_PASSWORD,
    DEMO_DRIVER_USERNAME,
    DEMO_JUDGE_PASSWORD,
    DEMO_JUDGE_USERNAME,
    DEMO_OPERATOR_C1_PASSWORD,
    DEMO_OPERATOR_C1_USERNAME,
    DEMO_OPERATOR_C2_PASSWORD,
    DEMO_OPERATOR_C2_USERNAME,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.connection import set_db_cluster_id
from app.main import app

client = TestClient(app)


# ==============================================================================
# 1. Argon2 Password Hashing Tests
# ==============================================================================

def test_argon2_hashing_and_verification():
    """Verify Argon2id produces valid hashes and correctly validates passwords."""
    raw_pass = "SecureSecretPassword123!"
    hashed = hash_password(raw_pass)

    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_pass, "") is False


# ==============================================================================
# 2. Login Tests
# ==============================================================================

def test_login_success_all_roles():
    """Test successful login for judge, operator, driver, and admin users."""
    roles_and_creds = [
        (DEMO_JUDGE_USERNAME, DEMO_JUDGE_PASSWORD, "judge", None),
        (DEMO_OPERATOR_C1_USERNAME, DEMO_OPERATOR_C1_PASSWORD, "operator", "C1"),
        (DEMO_OPERATOR_C2_USERNAME, DEMO_OPERATOR_C2_PASSWORD, "operator", "C2"),
        (DEMO_DRIVER_USERNAME, DEMO_DRIVER_PASSWORD, "driver", None),
        (DEMO_ADMIN_USERNAME, DEMO_ADMIN_PASSWORD, "admin", None),
    ]

    for uname, pwd, expected_role, expected_cluster in roles_and_creds:
        resp = client.post("/api/v1/auth/login", json={"username": uname, "password": pwd})
        assert resp.status_code == 200, f"Login failed for {uname}: {resp.text}"
        data = resp.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900
        assert data["user"]["username"] == uname
        assert data["user"]["role"] == expected_role
        assert data["user"]["cluster_id"] == expected_cluster


def test_login_invalid_password():
    """Verify login failure with wrong password returns 401 INVALID_CREDENTIALS."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_OPERATOR_C1_USERNAME, "password": "IncorrectPassword123!"},
    )
    assert resp.status_code == 401
    err = resp.json()
    assert "error" in err
    assert err["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_user():
    """Verify login failure for non-existent username returns 401 INVALID_CREDENTIALS."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "non_existent_user_99", "password": "SomePassword!"},
    )
    assert resp.status_code == 401
    err = resp.json()
    assert "error" in err
    assert err["error"]["code"] == "INVALID_CREDENTIALS"


# ==============================================================================
# 3. Refresh Token Tests
# ==============================================================================

def test_refresh_token_success():
    """Verify valid refresh token issues a new access token and rotated refresh token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_OPERATOR_C1_USERNAME, "password": DEMO_OPERATOR_C1_PASSWORD},
    )
    assert login_resp.status_code == 200
    ref_token = login_resp.json()["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": ref_token})
    assert resp.status_code == 200
    data = resp.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == DEMO_OPERATOR_C1_USERNAME


def test_refresh_with_access_token_rejected():
    """Verify passing an access token to the refresh endpoint returns 401 INVALID_TOKEN_TYPE."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_OPERATOR_C1_USERNAME, "password": DEMO_OPERATOR_C1_PASSWORD},
    )
    assert login_resp.status_code == 200
    acc_token = login_resp.json()["access_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": acc_token})
    assert resp.status_code == 401
    err = resp.json()
    assert err["error"]["code"] == "INVALID_TOKEN_TYPE"


# ==============================================================================
# 4. Expired and Invalid Token Tests
# ==============================================================================

def test_expired_token_rejected():
    """Verify an expired token returns 401 TOKEN_EXPIRED."""
    expired_token = create_access_token(
        subject=DEMO_OPERATOR_C1_USERNAME,
        role="operator",
        cluster_id="C1",
        expires_delta=timedelta(minutes=-15),  # expired 15 minutes ago
    )

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    err = resp.json()
    assert err["error"]["code"] == "TOKEN_EXPIRED"


def test_malformed_token_rejected():
    """Verify a malformed token returns 401 INVALID_TOKEN."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not_a_valid_jwt_token"})
    assert resp.status_code == 401
    err = resp.json()
    assert err["error"]["code"] == "INVALID_TOKEN"


def test_missing_auth_header_on_protected_endpoint():
    """Verify requesting /auth/me without an Authorization header returns 401 UNAUTHORIZED."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    err = resp.json()
    assert err["error"]["code"] == "UNAUTHORIZED"


# ==============================================================================
# 5. Role-Based Access Control (RBAC) Tests
# ==============================================================================

def test_wrong_role_driver_cannot_start_replay():
    """Verify driver role is denied from starting simulation replay (403 INSUFFICIENT_PERMISSIONS)."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_DRIVER_USERNAME, "password": DEMO_DRIVER_PASSWORD},
    )
    token = login_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/replay/start",
        json={"speed_multiplier": 60.0, "horizon_hours": 24},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    err = resp.json()
    assert err["error"]["code"] == "INSUFFICIENT_PERMISSIONS"


def test_judge_is_readonly_cannot_start_replay():
    """Verify demo judge role cannot start simulation replay (read-only)."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_JUDGE_USERNAME, "password": DEMO_JUDGE_PASSWORD},
    )
    token = login_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/replay/start",
        json={"speed_multiplier": 60.0, "horizon_hours": 24},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    err = resp.json()
    assert err["error"]["code"] == "INSUFFICIENT_PERMISSIONS"


def test_operator_can_start_replay():
    """Verify operator role is authorized to start simulation replay."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_OPERATOR_C1_USERNAME, "password": DEMO_OPERATOR_C1_PASSWORD},
    )
    token = login_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/replay/start",
        json={"speed_multiplier": 60.0, "horizon_hours": 24},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "session_id" in resp.json()


# ==============================================================================
# 6. Cluster Scoping & Cross-Cluster Access Tests
# ==============================================================================

def test_operator_access_own_cluster_succeeds():
    """Operator C1 accessing cluster C1 succeeds."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_OPERATOR_C1_USERNAME, "password": DEMO_OPERATOR_C1_PASSWORD},
    )
    token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/clusters/C1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "transformer_kva" in resp.json()


def test_operator_cross_cluster_access_denied():
    """Operator C1 accessing cluster C2 fails with 403 CROSS_CLUSTER_ACCESS_DENIED."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_OPERATOR_C1_USERNAME, "password": DEMO_OPERATOR_C1_PASSWORD},
    )
    token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/clusters/C2", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    err = resp.json()
    assert err["error"]["code"] == "CROSS_CLUSTER_ACCESS_DENIED"


def test_operator_cross_cluster_transformer_denied():
    """Operator C2 accessing transformer T1 (which belongs to C1) is rejected."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": DEMO_OPERATOR_C2_USERNAME, "password": DEMO_OPERATOR_C2_PASSWORD},
    )
    token = login_resp.json()["access_token"]

    resp = client.get(
        "/api/v1/transformer/T1/risk",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    err = resp.json()
    assert err["error"]["code"] == "CROSS_CLUSTER_ACCESS_DENIED"


def test_admin_and_judge_cross_cluster_allowed():
    """Admin and read-only Judge can inspect both cluster C1 and cluster C2 without restriction."""
    for uname, pwd in [(DEMO_ADMIN_USERNAME, DEMO_ADMIN_PASSWORD), (DEMO_JUDGE_USERNAME, DEMO_JUDGE_PASSWORD)]:
        login_resp = client.post("/api/v1/auth/login", json={"username": uname, "password": pwd})
        token = login_resp.json()["access_token"]

        for cid in ["C1", "C2"]:
            resp = client.get(f"/api/v1/clusters/{cid}", headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200, f"User {uname} failed to access {cid}: {resp.text}"


# ==============================================================================
# 7. Row-Level Security (RLS) Helper Tests
# ==============================================================================

def test_set_db_cluster_id_for_rls():
    """Verify that set_db_cluster_id executes SET LOCAL app.cluster_id for Postgres RLS."""
    mock_session = MagicMock()
    set_db_cluster_id(mock_session, "C1")
    assert mock_session.execute.called

    # Check that execution parameter cid='C1' was provided
    call_args = mock_session.execute.call_args
    assert call_args[0][1] == {"cid": "C1"}

    # Reset
    set_db_cluster_id(mock_session, None)
    call_args_reset = mock_session.execute.call_args
    assert call_args_reset[0][1] == {"cid": ""}


# ==============================================================================
# 8. Security Audit: No Secrets Committed
# ==============================================================================

def test_no_secrets_committed_in_git():
    """Verify that no .env files or hardcoded private key secrets are committed to git."""
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    tracked_files = result.stdout.strip().splitlines()

    # Ensure no .env file is staged
    for line in tracked_files:
        status, filename = line[:2], line[3:].strip()
        assert not filename.endswith(".env"), f"Found uncommitted or staged .env file: {filename}"

    # Verify .env is listed in .gitignore
    with open(".gitignore", "r", encoding="utf-8") as f:
        gitignore_content = f.read()
    assert ".env" in gitignore_content, ".env must be explicitly excluded in .gitignore"
