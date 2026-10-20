"""
FastAPI REST API service with salted password authentication and splash screen.
"""

import io
import os
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

from qr_architect.models import QRConfig, GenerationResult, ValidationReport
from qr_architect.generator import generate_qr
from qr_architect.validator import verify_qr_image
from qr_architect.presets import PRESETS
from qr_architect.auth import (
    LoginRequest,
    AuthStatus,
    verify_password,
    get_configured_password_hash,
    create_session_token,
    verify_session_token,
    COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS
)

app = FastAPI(
    title="QR Architect API",
    description="Engine for generating customized, styled QR codes with embedded logos, link retention verification, and password protection.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session_token_from_request(request: Request) -> str:
    """Extract token from cookie or Authorization header."""
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        return cookie_token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return ""


def require_auth(request: Request):
    """Dependency enforcing that the request carries a valid session token."""
    token = get_session_token_from_request(request)
    if not verify_session_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please unlock via the splash screen."
        )
    return True


@app.get("/api/health")
def health():
    """Public health check endpoint."""
    return {"status": "healthy", "service": "QR Architect", "version": "1.0.0"}


@app.get("/api/auth/status", response_model=AuthStatus)
def auth_status(request: Request):
    """Check whether current visitor has an active authenticated session."""
    token = get_session_token_from_request(request)
    is_authed = verify_session_token(token)
    return AuthStatus(authenticated=is_authed, requires_auth=True)


@app.post("/api/auth/login")
def auth_login(req: LoginRequest, response: Response):
    """Authenticate with salted/hashed password and establish session."""
    expected_hash = get_configured_password_hash()
    if not verify_password(req.password, expected_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Access denied."
        )

    token = create_session_token()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False  # Allow over HTTP for local/LAN or remote without strict HTTPS cert
    )
    return {"success": True, "token": token, "message": "Authenticated successfully"}


@app.post("/api/auth/logout")
def auth_logout(response: Response):
    """Log out and invalidate current session."""
    response.delete_cookie(key=COOKIE_NAME)
    return {"success": True, "message": "Logged out"}


@app.get("/api/presets", dependencies=[Depends(require_auth)])
def get_presets():
    """Return all available aesthetic presets (Protected)."""
    return PRESETS


@app.post("/api/generate", response_model=GenerationResult, dependencies=[Depends(require_auth)])
def api_generate(config: QRConfig):
    """
    Generate QR code from JSON configuration (Protected).
    Returns base64 data URI (for raster) or SVG string, plus validation report.
    """
    try:
        result = generate_qr(config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate/file", dependencies=[Depends(require_auth)])
def api_generate_file(config: QRConfig):
    """
    Generate QR code and return directly as a binary image response (Protected).
    """
    try:
        result = generate_qr(config)
        fmt = result.format.upper()
        if fmt == "SVG":
            return Response(content=result.svg_content, media_type="image/svg+xml")
        else:
            raw_b64 = result.image_base64.split(",", 1)[1]
            data = base64.b64decode(raw_b64)
            media_type = f"image/{fmt.lower()}"
            return Response(content=data, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/verify", response_model=ValidationReport, dependencies=[Depends(require_auth)])
async def api_verify(
    file: UploadFile = File(...),
    expected_data: str = Form(default="")
):
    """
    Upload an existing QR code image to decode and verify its link retention (Protected).
    """
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        report = verify_qr_image(img, expected_data)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")


# Mount static Web Dashboard
web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
