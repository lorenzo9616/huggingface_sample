"""FastAPI backend for the local AI generation app."""

import sqlite3
import os
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import ollama

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


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Local AI Generation App")


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.get("/models")
def list_models():
    """Return the list of locally available Ollama models."""
    try:
        result = ollama.list()
        models = [m.model for m in result.models]
        return {"models": models}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Ollama: {exc}")


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
    """Generate text with the specified Ollama model and save to the database."""
    try:
        result = ollama.generate(model=req.model_name, prompt=req.prompt)
        response_text = result.response
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Generation failed: {exc}")

    # Persist to SQLite
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
# Serve the frontend as static files
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
