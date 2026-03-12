"""FastAPI backend for the local AI generation app."""

import sqlite3
import os
import sys
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import ollama

# Add fish-audio-s2 to path so we can import the client
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "fish-audio-s2")
)
from fish_audio_client import FishAudioClient

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "insights.db")


def _get_db():
    """Return a connection to the SQLite database, creating the table if needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS insights (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt    TEXT    NOT NULL,
            response  TEXT    NOT NULL,
            model_used TEXT   NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class AddModelRequest(BaseModel):
    model_name: str


class GenerateRequest(BaseModel):
    prompt: str
    model_name: str


class TTSRequest(BaseModel):
    text: str
    reference_id: str | None = None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Local AI Generation App")

# Fish-Audio S2 client — connects to the local Fish-Audio server
FISH_AUDIO_URL = os.environ.get("FISH_AUDIO_URL", "http://localhost:8080")
fish_client = FishAudioClient(base_url=FISH_AUDIO_URL)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


FISH_AUDIO_TTS_PREFIX = "fish-audio:"


@app.get("/models")
def list_models():
    """Return Ollama models and Fish-Audio S2 TTS models in a unified list."""
    models = []

    # Ollama models (text generation)
    try:
        result = ollama.list()
        for m in result.models:
            models.append({"name": m.model, "type": "llm"})
    except Exception:
        pass  # Ollama may be offline — still show TTS models

    # Fish-Audio S2 models (text-to-speech)
    if fish_client.health():
        models.append({"name": f"{FISH_AUDIO_TTS_PREFIX}openaudio-s1-mini", "type": "tts"})

    if not models:
        raise HTTPException(
            status_code=502,
            detail="No models available. Ensure Ollama or Fish-Audio S2 is running.",
        )

    return {"models": models}


@app.post("/add-model")
def add_model(req: AddModelRequest):
    """Pull a model from the Ollama registry. This can be long-running."""
    model_name = req.model_name.strip()
    if not model_name:
        raise HTTPException(status_code=400, detail="model_name is required")

    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=600,  # 10-minute timeout for large models
        )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"ollama pull failed: {result.stderr.strip()}",
            )
        return {"status": "success", "model": model_name}
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail=f"Model download timed out after 10 minutes: {model_name}",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=502,
            detail="ollama CLI not found. Is Ollama installed?",
        )


@app.post("/generate")
def generate(req: GenerateRequest):
    """Generate content with the specified model.

    For Ollama (LLM) models: generates text and returns JSON.
    For Fish-Audio (TTS) models: generates speech and returns audio bytes.
    """
    # ── Fish-Audio TTS model ────────────────────────────────
    if req.model_name.startswith(FISH_AUDIO_TTS_PREFIX):
        try:
            audio_bytes = fish_client.tts(text=req.prompt)
        except ConnectionError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Fish-Audio S2 server unreachable: {exc}",
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        # Save to history
        conn = _get_db()
        try:
            conn.execute(
                "INSERT INTO insights (prompt, response, model_used) VALUES (?, ?, ?)",
                (req.prompt, "[audio generated]", req.model_name),
            )
            conn.commit()
        finally:
            conn.close()

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={"Content-Disposition": 'inline; filename="speech.wav"'},
        )

    # ── Ollama LLM model ────────────────────────────────────
    try:
        result = ollama.generate(model=req.model_name, prompt=req.prompt)
        response_text = result.response
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Generation failed: {exc}")

    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO insights (prompt, response, model_used) VALUES (?, ?, ?)",
            (req.prompt, response_text, req.model_name),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "prompt": req.prompt,
        "response": response_text,
        "model_used": req.model_name,
    }


@app.get("/history")
def history():
    """Return all past generations ordered by most recent first."""
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT id, prompt, response, model_used, timestamp "
            "FROM insights ORDER BY timestamp DESC"
        ).fetchall()
        return {"history": [dict(r) for r in rows]}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Fish-Audio S2 TTS endpoints
# ---------------------------------------------------------------------------


@app.get("/tts/health")
def tts_health():
    """Check if the Fish-Audio S2 server is reachable."""
    reachable = fish_client.health()
    return {"status": "online" if reachable else "offline", "url": FISH_AUDIO_URL}


@app.post("/tts")
def text_to_speech(req: TTSRequest):
    """Generate speech from text using Fish-Audio S2."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    try:
        audio_bytes = fish_client.tts(
            text=req.text,
            reference_id=req.reference_id,
        )
    except ConnectionError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Fish-Audio S2 server unreachable: {exc}",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="speech.wav"'},
    )


# ---------------------------------------------------------------------------
# Serve the frontend as static files
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
