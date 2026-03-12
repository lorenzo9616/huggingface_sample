# Local AI Generation App

A full-stack application for running AI text generation locally using [Ollama](https://ollama.com). All inference happens on your machine — no external API keys required.

## Architecture

```
huggingface_sample/
├── backend/          # FastAPI server
│   ├── main.py
│   └── requirements.txt
├── frontend/         # Vanilla HTML/CSS/JS UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── database/         # SQLite database & init script
│   └── init_db.py
├── claude.md         # AI agent project context
├── skills.md         # Developer command reference
└── README.md
```

## Prerequisites

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Ollama** — [ollama.com/download](https://ollama.com/download)

## Setup & Installation

### Step 1: Install Ollama

Download and install Ollama for your operating system from [ollama.com/download](https://ollama.com/download).

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download the installer from the Ollama website.

### Step 2: Start Ollama

Ollama usually starts automatically after installation. If not, open a terminal and run:

```bash
ollama serve
```

Leave this terminal open — Ollama needs to be running for the app to work.

### Step 3: Pull your first model

In a new terminal, download a model to get started:

```bash
ollama pull mistral
```

You can also pull models through the app's UI later. Other popular models: `llama3`, `phi3`, `gemma`.

### Step 4: Clone the repository

```bash
git clone <repo-url>
cd huggingface_sample
```

### Step 5: Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

> **Tip:** Use a virtual environment to keep dependencies isolated:
> ```bash
> python -m venv venv
> source venv/bin/activate   # Linux/macOS
> venv\Scripts\activate      # Windows
> pip install -r backend/requirements.txt
> ```

### Step 6: Initialize the database

```bash
python database/init_db.py
```

This creates `database/insights.db` with the `insights` table.

### Step 7: Start the backend server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 8: Open the app

Open your browser and navigate to:

```
http://localhost:8000
```

The FastAPI server serves the frontend automatically.

## Usage

### Managing models

1. The **Active Model** dropdown shows all models currently downloaded in Ollama.
2. Type a model name (e.g. `mistral`) in the **Add New Model** field and click **Add**. The download may take several minutes depending on the model size.
3. Click the **refresh** button to update the dropdown after adding models.

### Generating text

1. Select a model from the dropdown.
2. Type your prompt in the text area.
3. Click **Generate Insight** and wait for the response.
4. The prompt, response, and model used are automatically saved to the database.

### Viewing history

Click **Load History** to see all previous generations, ordered by most recent first.

## API Endpoints

| Method | Path         | Description                         |
|--------|--------------|-------------------------------------|
| GET    | `/models`    | List locally available Ollama models|
| POST   | `/add-model` | Pull a new model from Ollama        |
| POST   | `/generate`  | Generate text with a given prompt   |
| GET    | `/history`   | Fetch past generations from the DB  |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Could not reach Ollama" | Make sure `ollama serve` is running |
| "ollama CLI not found" | Install Ollama and ensure it's on your PATH |
| Model download times out | Large models may need more than 10 minutes — try pulling directly with `ollama pull <model>` |
| Port 8000 already in use | Change the port: `uvicorn backend.main:app --port 8001` |
