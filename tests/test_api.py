"""
Unit tests for FastAPI REST API endpoints including authentication.
"""

import io
from fastapi.testclient import TestClient
from qr_architect.api import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_unauthenticated_access_blocked():
    # Attempting to access protected endpoints without credentials must return 401
    res = client.get("/api/presets")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]

    res2 = client.post("/api/generate", json={"data": "https://example.com"})
    assert res2.status_code == 401


def test_auth_login_and_logout():
    # Bad password
    bad_res = client.post("/api/auth/login", json={"password": "wrong-password"})
    assert bad_res.status_code == 401

    # Good password (default is qr-admin-2026)
    good_res = client.post("/api/auth/login", json={"password": "qr-admin-2026"})
    assert good_res.status_code == 200
    assert good_res.json()["success"] is True
    assert "token" in good_res.json()

    # Session cookie is automatically stored in client
    status_res = client.get("/api/auth/status")
    assert status_res.status_code == 200
    assert status_res.json()["authenticated"] is True

    # Now protected routes should succeed
    presets_res = client.get("/api/presets")
    assert presets_res.status_code == 200
    assert "modern_tech" in presets_res.json()

    # Logout
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # Afterwards, protected routes should return 401 again
    blocked_again = client.get("/api/presets")
    assert blocked_again.status_code == 401


def test_authenticated_generation():
    # Log in
    login_res = client.post("/api/auth/login", json={"password": "qr-admin-2026"})
    assert login_res.status_code == 200

    payload = {
        "data": "https://antigravity.google.com/api-test",
        "colors": {
            "front_color": "#1e3a8a",
            "back_color": "#ffffff"
        },
        "module_style": "rounded",
        "format": "PNG"
    }
    res = client.post("/api/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["image_base64"].startswith("data:image/png;base64,")
    assert data["validation"]["matches_payload"] is True
    assert data["validation"]["decoded_text"] == "https://antigravity.google.com/api-test"


def test_authenticated_file_download_and_verify():
    # Log in
    client.post("/api/auth/login", json={"password": "qr-admin-2026"})

    gen_res = client.post("/api/generate/file", json={"data": "https://verify.example.com"})
    assert gen_res.status_code == 200
    assert gen_res.headers["content-type"] == "image/png"
    img_bytes = gen_res.content

    # Now post it to /api/verify
    files = {"file": ("test.png", io.BytesIO(img_bytes), "image/png")}
    data = {"expected_data": "https://verify.example.com"}
    res = client.post("/api/verify", files=files, data=data)
    assert res.status_code == 200
    val_data = res.json()
    assert val_data["is_valid"] is True
    assert val_data["matches_payload"] is True
    assert val_data["decoded_text"] == "https://verify.example.com"
