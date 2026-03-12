#!/usr/bin/env bash
# =============================================================================
# Start the Fish-Audio S2 API server
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
FISH_SPEECH_DIR="$SCRIPT_DIR/fish-speech"
CHECKPOINTS_DIR="$SCRIPT_DIR/checkpoints"

# Default to openaudio-s1-mini; override with first argument
MODEL="${1:-openaudio-s1-mini}"
MODEL_DIR="$CHECKPOINTS_DIR/$MODEL"
PORT="${2:-8080}"

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found. Run setup.sh first."
    exit 1
fi

if [ ! -d "$MODEL_DIR" ]; then
    echo "Error: Model weights not found at $MODEL_DIR"
    echo "Run setup.sh to download them, or specify a different model:"
    echo "  $0 <model-name> [port]"
    exit 1
fi

source "$VENV_DIR/bin/activate"
cd "$FISH_SPEECH_DIR"

echo "Starting Fish-Audio S2 API server..."
echo "  Model:    $MODEL"
echo "  Endpoint: http://0.0.0.0:$PORT"
echo "  TTS API:  POST http://localhost:$PORT/v1/tts"
echo ""

python -m tools.api_server \
    --listen "0.0.0.0:$PORT" \
    --llama-checkpoint-path "$MODEL_DIR" \
    --decoder-checkpoint-path "$MODEL_DIR/codec.pth" \
    --decoder-config-name modded_dac_vq
