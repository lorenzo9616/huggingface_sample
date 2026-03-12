# Project Overview

This is a **local AI text generation app** that connects to [Ollama](https://ollama.com) for running LLMs entirely on the user's machine. There is no external API dependency — all inference happens locally.

## Tech Stack

| Layer    | Technology              |
|----------|-------------------------|
| Backend  | Python 3.10+, FastAPI   |
| Frontend | Vanilla HTML / CSS / JS |
| Database | SQLite                  |
| AI       | Ollama (local models)   |
| TTS      | Fish-Audio S2 (local)   |

## Coding Rules

1. **Framework-free frontend** — No React, Vue, or any JS framework. Use plain `fetch()`, DOM manipulation, and semantic HTML.
2. **Robust error handling for long-running tasks** — Model downloads via `ollama pull` can take minutes. Always surface progress/status to the user and handle timeouts, cancellations, and failures gracefully.
3. **Relative API paths** — The frontend must call the backend using relative paths (e.g., `/models`, `/generate`) so the app works behind any reverse proxy or on any port without hard-coded URLs.
4. **Keep it simple** — Avoid unnecessary abstractions. One `main.py` for the backend, one `index.html` for the frontend.
5. **SQLite via stdlib** — Use Python's built-in `sqlite3` module. No ORM required.
6. **Fish-Audio S2 is optional** — The app must work without TTS. The frontend shows an online/offline badge and gracefully handles a missing TTS server. The Fish-Audio S2 server runs as a separate process on port 8080.
