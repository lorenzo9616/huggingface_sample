# Core Commands & Workflows

## Backend

### Install dependencies
```bash
pip install -r backend/requirements.txt
```

### Start the FastAPI server
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Run from the backend directory
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Ollama CLI

### Check installed models
```bash
ollama list
```

### Pull / download a new model
```bash
ollama pull <model-name>
# Example:
ollama pull mistral
```

### Run a model interactively (for testing)
```bash
ollama run <model-name>
```

### Start the Ollama background service
```bash
ollama serve
```
> On macOS / Linux, Ollama usually starts automatically after installation.
> If the backend cannot connect, run `ollama serve` in a separate terminal.

## Fish-Audio S2 (Text-to-Speech)

### Install Fish-Audio S2
```bash
cd fish-audio-s2
./setup.sh
```
This clones the repo, creates a venv, installs deps, and downloads the model.

### Start the Fish-Audio S2 API server
```bash
cd fish-audio-s2
./start_server.sh
# Or with a specific model and port:
./start_server.sh openaudio-s1-mini 8080
```
> The TTS API runs at `http://localhost:8080/v1/tts`.
> The FastAPI backend connects to it automatically.

### Test TTS from the command line
```bash
curl -X POST http://localhost:8080/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!"}' \
  --output test_speech.wav
```

### Use a custom Fish-Audio URL with the backend
```bash
FISH_AUDIO_URL=http://localhost:9090 uvicorn backend.main:app --reload
```

## Database

### Initialize the SQLite database
```bash
python database/init_db.py
```
This creates `database/insights.db` with the `insights` table.

## Frontend

### Serve the frontend (simple approach)
```bash
# From the project root — the FastAPI app serves static files automatically
# Just open http://localhost:8000 in your browser
```

### Or use Python's built-in HTTP server (standalone)
```bash
cd frontend
python -m http.server 3000
```
