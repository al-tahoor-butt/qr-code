/**
 * QR Architect Frontend Application Controller
 * Includes password authentication, splash screen gating, and real-time generation.
 */

// Application State
const state = {
  authenticated: false,
  data: "https://antigravity.google.com",
  colors: {
    front_color: "#1e293b",
    back_color: "#ffffff",
    gradient_type: "none",
    gradient_end_color: "#3b82f6",
    eye_outer_color: "#4338ca",
    eye_inner_color: "#06b6d4"
  },
  module_style: "rounded",
  eye_style: "rounded",
  error_correction: "H",
  logo: null,
  box_size: 14,
  border: 4,
  currentResult: null
};

let presets = {};
let debounceTimeout = null;

// DOM Elements - Splash Screen
const elSplashOverlay = document.getElementById("splash-overlay");
const elSplashForm = document.getElementById("splash-form");
const elSplashPassword = document.getElementById("splash-password");
const elSplashError = document.getElementById("splash-error");
const elBtnToggleEye = document.getElementById("btn-toggle-eye");
const elBtnUnlock = document.getElementById("btn-unlock");
const elBtnLogout = document.getElementById("btn-logout");

// DOM Elements - Main Controls
const elDataInput = document.getElementById("data-input");
const elFrontColor = document.getElementById("front-color");
const elBackColor = document.getElementById("back-color");
const elTransparentBg = document.getElementById("transparent-bg");
const elGradientType = document.getElementById("gradient-type");
const elGradientEndRow = document.getElementById("gradient-end-row");
const elGradientEndColor = document.getElementById("gradient-end-color");
const elEyeOuterColor = document.getElementById("eye-outer-color");
const elEyeInnerColor = document.getElementById("eye-inner-color");

const elLogoInput = document.getElementById("logo-input");
const elDropzone = document.getElementById("upload-dropzone");
const elLogoPreviewRow = document.getElementById("logo-preview-row");
const elLogoThumbnail = document.getElementById("logo-thumbnail");
const elBtnRemoveLogo = document.getElementById("btn-remove-logo");
const elLogoScale = document.getElementById("logo-scale");
const elLogoScaleVal = document.getElementById("logo-scale-val");
const elLogoShape = document.getElementById("logo-shape");
const elLogoPadding = document.getElementById("logo-padding");
const elLogoPaddingVal = document.getElementById("logo-padding-val");

const elEccSelect = document.getElementById("ecc-select");
const elPreviewImg = document.getElementById("preview-img");
const elStatusIndicator = document.getElementById("status-indicator");
const elStatusTitle = document.getElementById("status-title");
const elDecodedLink = document.getElementById("decoded-link");
const elMetricContrast = document.getElementById("metric-contrast");
const elMetricLogo = document.getElementById("metric-logo");
const elMetricEcc = document.getElementById("metric-ecc");
const elWarningBox = document.getElementById("warning-box");

const elBtnDownloadPng = document.getElementById("btn-download-png");
const elBtnDownloadSvg = document.getElementById("btn-download-svg");
const elBtnCopyImg = document.getElementById("btn-copy-img");

// Initialize on Load
document.addEventListener("DOMContentLoaded", async () => {
  setupSplashAuth();
  setupEventListeners();

  // Check initial authentication
  await checkAuthStatus();
});

// Check if user is currently authenticated
async function checkAuthStatus() {
  try {
    const res = await fetch("/api/auth/status");
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated) {
        unlockDashboard();
        return;
      }
    }
  } catch (err) {
    console.warn("Auth check failed:", err);
  }
  showSplashScreen();
}

function showSplashScreen() {
  state.authenticated = false;
  elSplashOverlay.classList.remove("hidden");
  elSplashPassword.value = "";
  elSplashError.style.display = "none";
  setTimeout(() => elSplashPassword.focus(), 100);
}

function unlockDashboard() {
  state.authenticated = true;
  elSplashOverlay.classList.add("hidden");
  loadPresets();
  triggerRender();
}

// Setup Splash Screen Authentication Listeners
function setupSplashAuth() {
  // Toggle password visibility
  elBtnToggleEye.addEventListener("click", () => {
    const isPassword = elSplashPassword.type === "password";
    elSplashPassword.type = isPassword ? "text" : "password";
    elBtnToggleEye.textContent = isPassword ? "🙈" : "👁️";
  });

  // Submit Password Form
  elSplashForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const password = elSplashPassword.value;
    if (!password) return;

    elBtnUnlock.disabled = true;
    elBtnUnlock.innerHTML = "<span>Verifying...</span>";
    elSplashError.style.display = "none";

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password })
      });

      if (res.ok) {
        unlockDashboard();
      } else {
        const err = await res.json();
        elSplashError.textContent = err.detail || "Incorrect password. Access denied.";
        elSplashError.style.display = "block";
        elSplashPassword.focus();
        elSplashPassword.select();
      }
    } catch (err) {
      elSplashError.textContent = "Connection error. Is the server running?";
      elSplashError.style.display = "block";
    } finally {
      elBtnUnlock.disabled = false;
      elBtnUnlock.innerHTML = "<span>Unlock Dashboard</span>";
    }
  });

  // Logout Button
  elBtnLogout.addEventListener("click", async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (err) {
      console.warn("Logout error:", err);
    }
    showSplashScreen();
  });
}

// Load presets from API
async function loadPresets() {
  try {
    const res = await fetch("/api/presets");
    if (res.status === 401) {
      showSplashScreen();
      return;
    }
    if (res.ok) {
      presets = await res.json();
      renderPresetChips();
    }
  } catch (err) {
    console.warn("Could not load presets from API:", err);
  }
}

// Render preset chips in UI
function renderPresetChips() {
  const container = document.getElementById("presets-container");
  if (!container) return;
  container.innerHTML = "";

  Object.entries(presets).forEach(([key, p]) => {
    const chip = document.createElement("div");
    chip.className = `preset-chip ${key === "modern_tech" ? "active" : ""}`;
    chip.setAttribute("data-preset", key);

    const dots = document.createElement("div");
    dots.className = "preset-dots";

    const c1 = document.createElement("span");
    c1.className = "color-dot";
    c1.style.backgroundColor = p.colors.front_color;

    const c2 = document.createElement("span");
    c2.className = "color-dot";
    c2.style.backgroundColor = p.colors.eye_outer_color || p.colors.front_color;

    const c3 = document.createElement("span");
    c3.className = "color-dot";
    c3.style.backgroundColor = p.colors.eye_inner_color || p.colors.front_color;

    dots.appendChild(c1);
    dots.appendChild(c2);
    dots.appendChild(c3);

    const name = document.createElement("span");
    name.className = "preset-name";
    name.textContent = p.name;

    chip.appendChild(dots);
    chip.appendChild(name);

    chip.addEventListener("click", () => applyPreset(key));
    container.appendChild(chip);
  });
}

// Apply selected preset
function applyPreset(key) {
  const p = presets[key];
  if (!p) return;

  document.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
  const activeChip = document.querySelector(`[data-preset="${key}"]`);
  if (activeChip) activeChip.classList.add("active");

  state.colors.front_color = p.colors.front_color;
  state.colors.back_color = p.colors.back_color;
  state.colors.gradient_type = p.colors.gradient_type || "none";
  state.colors.gradient_end_color = p.colors.gradient_end_color || "#3b82f6";
  state.colors.eye_outer_color = p.colors.eye_outer_color || p.colors.front_color;
  state.colors.eye_inner_color = p.colors.eye_inner_color || p.colors.front_color;

  state.module_style = p.module_style;
  state.eye_style = p.eye_style;
  state.error_correction = p.error_correction;

  syncInputsFromState();
  triggerRender();
}

// Sync inputs to match state
function syncInputsFromState() {
  elFrontColor.value = state.colors.front_color;
  document.getElementById("front-hex").textContent = state.colors.front_color;

  if (state.colors.back_color.toLowerCase() === "transparent") {
    elTransparentBg.checked = true;
    elBackColor.disabled = true;
  } else {
    elTransparentBg.checked = false;
    elBackColor.disabled = false;
    elBackColor.value = state.colors.back_color;
    document.getElementById("back-hex").textContent = state.colors.back_color;
  }

  elGradientType.value = state.colors.gradient_type;
  elGradientEndRow.style.display = state.colors.gradient_type !== "none" ? "flex" : "none";
  if (state.colors.gradient_end_color) {
    elGradientEndColor.value = state.colors.gradient_end_color;
    document.getElementById("grad-end-hex").textContent = state.colors.gradient_end_color;
  }

  if (state.colors.eye_outer_color) {
    elEyeOuterColor.value = state.colors.eye_outer_color;
    document.getElementById("eye-outer-hex").textContent = state.colors.eye_outer_color;
  }
  if (state.colors.eye_inner_color) {
    elEyeInnerColor.value = state.colors.eye_inner_color;
    document.getElementById("eye-inner-hex").textContent = state.colors.eye_inner_color;
  }

  document.querySelectorAll("[data-module-style]").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-module-style") === state.module_style);
  });
  document.querySelectorAll("[data-eye-style]").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-eye-style") === state.eye_style);
  });

  elEccSelect.value = state.error_correction;
}

// Setup Event Listeners
function setupEventListeners() {
  elDataInput.addEventListener("input", (e) => {
    state.data = e.target.value.trim() || "https://antigravity.google.com";
    triggerRender();
  });

  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const val = btn.getAttribute("data-value");
      elDataInput.value = val;
      state.data = val;
      triggerRender();
    });
  });

  elFrontColor.addEventListener("input", (e) => {
    state.colors.front_color = e.target.value;
    document.getElementById("front-hex").textContent = e.target.value;
    triggerRender();
  });

  elBackColor.addEventListener("input", (e) => {
    state.colors.back_color = e.target.value;
    document.getElementById("back-hex").textContent = e.target.value;
    triggerRender();
  });

  elTransparentBg.addEventListener("change", (e) => {
    if (e.target.checked) {
      state.colors.back_color = "transparent";
      elBackColor.disabled = true;
    } else {
      state.colors.back_color = elBackColor.value;
      elBackColor.disabled = false;
    }
    triggerRender();
  });

  elGradientType.addEventListener("change", (e) => {
    state.colors.gradient_type = e.target.value;
    elGradientEndRow.style.display = e.target.value !== "none" ? "flex" : "none";
    triggerRender();
  });

  elGradientEndColor.addEventListener("input", (e) => {
    state.colors.gradient_end_color = e.target.value;
    document.getElementById("grad-end-hex").textContent = e.target.value;
    triggerRender();
  });

  elEyeOuterColor.addEventListener("input", (e) => {
    state.colors.eye_outer_color = e.target.value;
    document.getElementById("eye-outer-hex").textContent = e.target.value;
    triggerRender();
  });

  elEyeInnerColor.addEventListener("input", (e) => {
    state.colors.eye_inner_color = e.target.value;
    document.getElementById("eye-inner-hex").textContent = e.target.value;
    triggerRender();
  });

  document.querySelectorAll("[data-module-style]").forEach(b => {
    b.addEventListener("click", () => {
      document.querySelectorAll("[data-module-style]").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      state.module_style = b.getAttribute("data-module-style");
      triggerRender();
    });
  });

  document.querySelectorAll("[data-eye-style]").forEach(b => {
    b.addEventListener("click", () => {
      document.querySelectorAll("[data-eye-style]").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      state.eye_style = b.getAttribute("data-eye-style");
      triggerRender();
    });
  });

  elEccSelect.addEventListener("change", (e) => {
    state.error_correction = e.target.value;
    triggerRender();
  });

  // Dropzone drag & drop
  elDropzone.addEventListener("click", () => elLogoInput.click());
  elDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    elDropzone.style.borderColor = "var(--primary)";
  });
  elDropzone.addEventListener("dragleave", () => {
    elDropzone.style.borderColor = "var(--border-color)";
  });
  elDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    elDropzone.style.borderColor = "var(--border-color)";
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleLogoFile(e.dataTransfer.files[0]);
    }
  });

  elLogoInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleLogoFile(e.target.files[0]);
    }
  });

  elBtnRemoveLogo.addEventListener("click", () => {
    state.logo = null;
    elLogoPreviewRow.style.display = "none";
    elLogoInput.value = "";
    triggerRender();
  });

  document.getElementById("btn-sample-logo").addEventListener("click", async () => {
    try {
      const imgRes = await fetch("/examples/sample_logo.png");
      if (imgRes.ok) {
        const blob = await imgRes.blob();
        handleLogoFile(blob);
      } else {
        setLogoFromPath("examples/sample_logo.png");
      }
    } catch (err) {
      setLogoFromPath("examples/sample_logo.png");
    }
  });

  elLogoScale.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    elLogoScaleVal.textContent = `${Math.round(val * 100)}%`;
    if (state.logo) {
      state.logo.scale = val;
      triggerRender();
    }
  });

  elLogoShape.addEventListener("change", (e) => {
    if (state.logo) {
      state.logo.shape = e.target.value;
      triggerRender();
    }
  });

  elLogoPadding.addEventListener("input", (e) => {
    const val = parseInt(e.target.value, 10);
    elLogoPaddingVal.textContent = `${val}px`;
    if (state.logo) {
      state.logo.padding = val;
      triggerRender();
    }
  });

  elBtnDownloadPng.addEventListener("click", downloadPng);
  elBtnDownloadSvg.addEventListener("click", downloadSvg);
  elBtnCopyImg.addEventListener("click", copyImageToClipboard);
}

// Handle Logo File to base64
function handleLogoFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    const base64Data = e.target.result;
    elLogoThumbnail.src = base64Data;
    elLogoPreviewRow.style.display = "flex";

    state.logo = {
      image_base64: base64Data,
      scale: parseFloat(elLogoScale.value),
      shape: elLogoShape.value,
      padding: parseInt(elLogoPadding.value, 10),
      bg_color: "#ffffff"
    };

    if (state.error_correction === "L" || state.error_correction === "M") {
      state.error_correction = "H";
      elEccSelect.value = "H";
    }

    triggerRender();
  };
  reader.readAsDataURL(file);
}

function setLogoFromPath(path) {
  state.logo = {
    image_path: path,
    scale: parseFloat(elLogoScale.value),
    shape: elLogoShape.value,
    padding: parseInt(elLogoPadding.value, 10),
    bg_color: "#ffffff"
  };
  elLogoPreviewRow.style.display = "flex";
  elLogoThumbnail.src = path;
  if (state.error_correction === "L" || state.error_correction === "M") {
    state.error_correction = "H";
    elEccSelect.value = "H";
  }
  triggerRender();
}

function triggerRender() {
  if (!state.authenticated) return;
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(renderQR, 120);
}

async function renderQR() {
  if (!state.authenticated) return;
  try {
    const payload = {
      data: state.data,
      colors: state.colors,
      module_style: state.module_style,
      eye_style: state.eye_style,
      error_correction: state.error_correction,
      logo: state.logo,
      box_size: state.box_size,
      border: state.border,
      format: "PNG"
    };

    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.status === 401) {
      showSplashScreen();
      return;
    }

    if (!res.ok) {
      const err = await res.json();
      console.error("API error:", err);
      return;
    }

    const data = await res.json();
    state.currentResult = data;
    updateUIWithResult(data);
  } catch (err) {
    console.error("Failed to generate QR code:", err);
  }
}

function updateUIWithResult(result) {
  if (result.image_base64) {
    elPreviewImg.src = result.image_base64;
  }

  const val = result.validation;

  if (val.is_valid && val.matches_payload) {
    elStatusIndicator.className = "status-indicator";
    elStatusTitle.textContent = "Link Verified & 100% Scannable";
    elStatusTitle.style.color = "var(--accent-green)";
  } else if (val.is_valid && !val.matches_payload) {
    elStatusIndicator.className = "status-indicator invalid";
    elStatusTitle.textContent = "Warning: Extracted Link Mismatch!";
    elStatusTitle.style.color = "var(--warning)";
  } else {
    elStatusIndicator.className = "status-indicator invalid";
    elStatusTitle.textContent = "Error: Unscannable QR Code";
    elStatusTitle.style.color = "var(--danger)";
  }

  elDecodedLink.textContent = val.decoded_text || "(Barcode scanner could not decode)";
  elMetricContrast.textContent = `${val.contrast_ratio}:1`;
  elMetricContrast.style.color = val.contrast_ratio >= 4.5 ? "var(--accent-green)" : "var(--danger)";
  elMetricLogo.textContent = `${val.logo_coverage_pct}%`;
  elMetricEcc.textContent = `Level ${val.error_correction}`;

  if (val.warnings && val.warnings.length > 0) {
    elWarningBox.style.display = "block";
    elWarningBox.innerHTML = `<strong>Scanning Alert:</strong><br>${val.warnings.join("<br>")}`;
  } else {
    elWarningBox.style.display = "none";
  }
}

function downloadPng() {
  if (!state.currentResult || !state.currentResult.image_base64) return;
  const link = document.createElement("a");
  link.download = `qrcode_${Date.now()}.png`;
  link.href = state.currentResult.image_base64;
  link.click();
}

async function downloadSvg() {
  try {
    const payload = {
      data: state.data,
      colors: state.colors,
      module_style: state.module_style,
      eye_style: state.eye_style,
      error_correction: state.error_correction,
      logo: state.logo,
      box_size: state.box_size,
      border: state.border,
      format: "SVG"
    };

    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (res.status === 401) {
      showSplashScreen();
      return;
    }

    if (res.ok) {
      const data = await res.json();
      const blob = new Blob([data.svg_content], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.download = `qrcode_${Date.now()}.svg`;
      link.href = url;
      link.click();
      URL.revokeObjectURL(url);
    }
  } catch (err) {
    console.error("Failed to download SVG:", err);
  }
}

async function copyImageToClipboard() {
  if (!state.currentResult || !state.currentResult.image_base64) return;
  try {
    const res = await fetch(state.currentResult.image_base64);
    const blob = await res.blob();
    await navigator.clipboard.write([
      new ClipboardItem({ [blob.type]: blob })
    ]);
    const btn = elBtnCopyImg;
    const oldText = btn.innerHTML;
    btn.innerHTML = "✓ Copied to Clipboard!";
    setTimeout(() => { btn.innerHTML = oldText; }, 2000);
  } catch (err) {
    alert("Could not copy to clipboard. Download PNG instead.");
  }
}
