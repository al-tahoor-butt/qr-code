# QR Architect 🏛️

A production-grade architecture for generating custom-styled QR codes with custom colors, gradients, module geometry, and embedded center logos **while mathematically guaranteeing link retention and scannability**.

Includes a **salted & hashed password-protected splash screen** for secure public/remote web access.

---

## 🌐 Live Web Access

The web dashboard is published and live on GitHub Pages:

🔗 **[https://al-tahoor-butt.github.io/qr-code/](https://al-tahoor-butt.github.io/qr-code/)**

- **Splash Screen Authentication**: When accessing the site, users are gated by a secure password modal.
- **Default Access Password**: `qr-admin-2026`
- **Security Standard**: Uses **PBKDF2-HMAC-SHA256 with 100,000 iterations and a cryptographically random salt**. Verification runs in-browser via the native Web Cryptography API (`crypto.subtle`) for GitHub Pages, and in Python for backend/Docker deployments.

---

## 🌟 Key Capabilities

- **Mathematical Link Retention**:
  - Automatically enforces **Reed-Solomon Error Correction Level H (~30% recovery capacity)** or Level Q (~25%) when embedding logos.
  - Automatically clamps embedded logo scale to safe bounds ($\le 28\%$ of total QR dimension, default $22\%$) so data modules and finder patterns are never critically occluded.
  - Adds an automatic anti-bleed quiet margin around logos so camera binarization algorithms cleanly separate data dots from the logo artwork.
  - Integrated with **`zxing-cpp`** for automated decode & link retention verification.

- **Full Palette & Gradient Customization**:
  - **Foreground modules**: Solid colors or gradients (Linear Horizontal, Linear Vertical, Linear Diagonal, Radial).
  - **Background**: Solid color or full **alpha transparency** for overlaying onto posters, flyers, or websites.
  - **Independent Eye Styling**: Custom colors and shapes for the 3 corner finder pattern outer frames and inner balls.
  - **Module Geometries**: Rounded, Circular Dots, Classic Squares, and Gapped Squares.

- **Dual-Mode Vector & High-Res Raster Export**:
  - **PNG / JPEG / WebP**: Crisp raster exports up to print resolution (1024px, 2048px).
  - **SVG Vector**: Clean, infinite-resolution vector graphics with native SVG gradients and embedded images.

- **Multi-Interface Architecture**:
  - **Public Web Dashboard**: Published to GitHub Pages with client-side WebCrypto authentication.
  - **Python SDK**: High-level typed API (`generate_qr`, `verify_qr_image`, `QRConfig`).
  - **CLI Tool (`qr-gen`)**: Command-line generator, verifier, and password manager (`./qr_gen set-password`).
  - **REST API (FastAPI)**: High-performance backend endpoints with session token auth and Swagger UI (`/docs`).
  - **Docker Container**: Instant 1-click deployment with `Dockerfile` and `docker-compose.yml`.

---

## 🔐 Password Security & Splash Screen

### Changing the Password

#### Option 1: For the Local / Backend Server
Run the CLI tool to generate a new salted PBKDF2 hash:
```bash
./qr_gen set-password
```
Or specify the password via environment variables:
```bash
export APP_PASSWORD="MyNewSecretPassword"
./qr_gen serve
```

#### Option 2: For GitHub Pages (Client-Side Mode)
1. Generate your salted hash:
   ```bash
   ./qr_gen set-password -p "MyNewSecretPassword"
   ```
2. Update the `AUTH_CONFIG` in [web/app.js](file:///home/alty/projects/qr-code/web/app.js):
   ```javascript
   const AUTH_CONFIG = {
     iterations: 100000,
     saltHex: "<your_salt_hex>",
     hashHex: "<your_hash_hex>"
   };
   ```
3. Commit and push: GitHub Actions will automatically redeploy the updated hash to GitHub Pages in ~30 seconds.

---

## 🚀 Local Quick Start

### 1. Installation

```bash
cd /home/alty/projects/qr-code
source .venv/bin/activate
pip install -e .
```

### 2. Run the Local Server & Dashboard

```bash
./qr_gen serve --port 8000
```
Open **http://localhost:8000** in your browser and enter `qr-admin-2026`.

### 3. Using the Executable CLI (`./qr_gen`)

```bash
# Generate a styled QR code with custom colors and logo
./qr_gen generate \
  --data "https://antigravity.google.com" \
  --fg "#1e3a8a" \
  --bg "#ffffff" \
  --eye-outer "#1d4ed8" \
  --eye-inner "#0284c7" \
  --module-style rounded \
  --logo examples/sample_logo.png \
  --output custom_qr.png
```

```bash
# Verify link retention on an existing QR code
./qr_gen verify custom_qr.png --expected "https://antigravity.google.com"
```

---

## 🐳 Docker Deployment (Self-Hosted Remote Web Access)

Run with Docker Compose:
```bash
docker compose up -d
```
Access at `http://your-server-ip:8000`.

---

## 🧪 Automated Test Suite

Run all 15 unit tests with pytest:
```bash
.venv/bin/pytest -v
```
Tests cover:
- PBKDF2 salting, hash generation, and constant-time verification
- Session token creation, signing, and tampering protection
- Unauthenticated route blocking (401 Unauthorized)
- Color, gradient, eye shape, and module shape customization
- Logo embedding within safe error correction thresholds
- ZXing-CPP barcode decoding and link payload matching
