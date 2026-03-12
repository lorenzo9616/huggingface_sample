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
