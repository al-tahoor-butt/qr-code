"""
Authentication module for QR Architect.
Provides salted and hashed password security using PBKDF2-HMAC-SHA256,
constant-time verification, and HMAC-signed session management.
"""

import os
import hmac
import hashlib
import secrets
import time
from typing import Optional
from pydantic import BaseModel


# Standard iterations for PBKDF2
PBKDF2_ITERATIONS = 100_000
SESSION_MAX_AGE_SECONDS = 7 * 24 * 3600  # 7 days
COOKIE_NAME = "qr_session"

# Default fallback credentials for 'qr-admin-2026'
DEFAULT_SALT_HEX = "e9b5d78243b6716b7628b2bc6dda48ff"
DEFAULT_HASH_HEX = "eadbbf40bf25ec9ca94e823ff188c8e9dad5e2e94899a29a151988e8873c0171"
DEFAULT_STORED_HASH = f"pbkdf2:sha256:{PBKDF2_ITERATIONS}:{DEFAULT_SALT_HEX}:{DEFAULT_HASH_HEX}"


def generate_secret_key() -> str:
    """Generate a persistent or fallback random HMAC secret key."""
    env_secret = os.environ.get("APP_SECRET_KEY")
    if env_secret:
        return env_secret
    return secrets.token_hex(32)


SECRET_KEY = generate_secret_key().encode("utf-8")


def hash_password(password: str, salt: Optional[bytes] = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with a cryptographically secure random salt.
    Format: pbkdf2:sha256:<iterations>:<salt_hex>:<hash_hex>
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2:sha256:{iterations}:{salt.hex()}:{dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a plaintext password against a salted PBKDF2 hash using constant-time comparison.
    """
    try:
        parts = stored_hash.split(":")
        if len(parts) != 5 or parts[0] != "pbkdf2" or parts[1] != "sha256":
            return False
        iterations = int(parts[2])
        salt = bytes.fromhex(parts[3])
        expected_hash = bytes.fromhex(parts[4])
        computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception:
        return False


def get_configured_password_hash() -> str:
    """
    Retrieve or initialize the system password hash from environment.
    Supports:
    1. APP_PASSWORD_HASH: Pre-computed hash string
    2. APP_PASSWORD: Plaintext password (hashed with random salt)
    3. Fallback default: 'qr-admin-2026'
    """
    stored = os.environ.get("APP_PASSWORD_HASH")
    if stored:
        return stored.strip()

    raw_password = os.environ.get("APP_PASSWORD")
    if raw_password:
        computed = hash_password(raw_password)
        os.environ["APP_PASSWORD_HASH"] = computed
        return computed

    return DEFAULT_STORED_HASH


def create_session_token() -> str:
    """
    Create a signed, tamper-proof session token: <timestamp>:<nonce>:<signature>
    """
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    payload = f"{timestamp}:{nonce}".encode("utf-8")
    sig = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()
    return f"{timestamp}:{nonce}:{sig}"


def verify_session_token(token: Optional[str]) -> bool:
    """
    Verify signature and freshness of a session token.
    """
    if not token:
        return False
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False
        timestamp_str, nonce, sig = parts
        ts = int(timestamp_str)
        now = int(time.time())

        # Expiration check
        if now - ts > SESSION_MAX_AGE_SECONDS or ts > now + 300:
            return False

        payload = f"{timestamp_str}:{nonce}".encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False


class LoginRequest(BaseModel):
    password: str


class AuthStatus(BaseModel):
    authenticated: bool
    requires_auth: bool = True
