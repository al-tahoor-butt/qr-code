"""
Unit tests for authentication, password hashing, and session management.
"""

import time
from qr_architect.auth import (
    hash_password,
    verify_password,
    create_session_token,
    verify_session_token,
    PBKDF2_ITERATIONS
)


def test_password_hashing_and_verification():
    password = "SuperSecretPassword123!"
    h1 = hash_password(password)
    h2 = hash_password(password)

    # Different salts must yield different hash strings
    assert h1 != h2
    assert f"pbkdf2:sha256:{PBKDF2_ITERATIONS}:" in h1

    # Verification must succeed for correct password
    assert verify_password(password, h1) is True
    assert verify_password(password, h2) is True

    # Verification must fail for incorrect password
    assert verify_password("WrongPassword!", h1) is False
    assert verify_password("", h1) is False


def test_session_tokens():
    token = create_session_token()
    assert verify_session_token(token) is True

    # Tampered token must fail
    tampered = token[:-4] + "abcd"
    assert verify_session_token(tampered) is False

    # Empty or malformed token must fail
    assert verify_session_token("") is False
    assert verify_session_token("invalid:token") is False
