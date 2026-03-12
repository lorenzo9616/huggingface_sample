#!/usr/bin/env bash
# =============================================================================
# Fish-Audio S2 — Setup & Installation Script
# Follows: https://speech.fish.audio/install/
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECKPOINTS_DIR="$SCRIPT_DIR/checkpoints"
VENV_DIR="$SCRIPT_DIR/venv"

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Pre-flight checks ──────────────────────────────────────────────────────
echo "============================================="
echo "  Fish-Audio S2  —  Setup Script"
echo "============================================="
echo ""

# Check Python version
if ! command -v python3 &>/dev/null; then
    error "Python 3 is required but not found. Install Python 3.10+."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Found Python $PY_VERSION"

# Check git
if ! command -v git &>/dev/null; then
    error "git is required but not found."
    exit 1
fi

# Check GPU (optional — warn only)
if command -v nvidia-smi &>/dev/null; then
    info "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
    echo ""
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || echo "0")
    if [ "${GPU_MEM:-0}" -lt 12000 ]; then
        warn "Fish-Audio S2 recommends at least 12 GB VRAM (24 GB for S2-Pro)."
        warn "You have ~${GPU_MEM} MB. The mini model may still work."
    fi
else
    warn "No NVIDIA GPU detected. CPU-only mode will be used (much slower)."
fi

# ── Step 1: Clone fish-speech repo ─────────────────────────────────────────
FISH_SPEECH_DIR="$SCRIPT_DIR/fish-speech"

if [ -d "$FISH_SPEECH_DIR" ]; then
    info "fish-speech repo already cloned at $FISH_SPEECH_DIR"
    cd "$FISH_SPEECH_DIR"
    git pull --ff-only || warn "Could not update repo (not on a clean branch?)"
else
    info "Cloning fishaudio/fish-speech..."
    git clone https://github.com/fishaudio/fish-speech.git "$FISH_SPEECH_DIR"
    cd "$FISH_SPEECH_DIR"
fi

# ── Step 2: Create virtual environment ─────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
info "Activated venv: $(which python)"

# Upgrade pip
pip install --upgrade pip setuptools wheel

# ── Step 3: Install fish-speech with dependencies ──────────────────────────
info "Installing fish-speech package..."

# Detect CUDA version for the right extras
if command -v nvidia-smi &>/dev/null; then
    CUDA_VER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 || echo "")
    if [ -n "$CUDA_VER" ]; then
        info "Installing with CUDA support (pip install -e .) ..."
        pip install -e . 2>&1 | tail -5
    fi
else
    info "Installing CPU-only (pip install -e .[cpu]) ..."
    pip install -e ".[cpu]" 2>&1 | tail -5
fi

# ── Step 4: Install huggingface_hub for model downloads ────────────────────
pip install "huggingface_hub[cli]"

# ── Step 5: Download model weights ─────────────────────────────────────────
echo ""
info "Downloading model weights..."

MINI_DIR="$CHECKPOINTS_DIR/openaudio-s1-mini"

if [ -d "$MINI_DIR" ] && [ "$(ls -A "$MINI_DIR" 2>/dev/null)" ]; then
    info "Model weights already present at $MINI_DIR"
else
    info "Downloading openaudio-s1-mini (~4 GB) ..."
    info "This may take a while depending on your connection."
    huggingface-cli download fishaudio/openaudio-s1-mini --local-dir "$MINI_DIR"
fi

# ── Step 6: Verify installation ───────────────────────────────────────────
echo ""
echo "============================================="
info "Installation complete!"
echo "============================================="
echo ""
echo "To activate the environment later:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To start the Fish-Audio S2 API server:"
echo "  cd $FISH_SPEECH_DIR"
echo "  python -m tools.api_server \\"
echo "    --listen 0.0.0.0:8080 \\"
echo "    --llama-checkpoint-path \"$MINI_DIR\" \\"
echo "    --decoder-checkpoint-path \"$MINI_DIR/codec.pth\" \\"
echo "    --decoder-config-name modded_dac_vq"
echo ""
echo "The API will be available at http://localhost:8080"
echo "TTS endpoint: POST http://localhost:8080/v1/tts"
echo ""
