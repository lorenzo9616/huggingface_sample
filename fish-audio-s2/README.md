# Fish-Audio S2 — Local TTS Module

This folder contains the setup and integration scripts for [Fish-Audio S2](https://speech.fish.audio/), an open-source text-to-speech model trained on 10M+ hours of audio across ~50 languages.

## Directory Layout

```
fish-audio-s2/
├── setup.sh            # One-command install script
├── start_server.sh     # Launch the Fish-Audio API server
├── fish_audio_client.py  # Python client for the /v1/tts endpoint
├── checkpoints/        # Model weights (downloaded by setup.sh)
├── references/         # Reference audio for voice cloning
│   └── default/
│       ├── sample.wav
│       └── sample.lab
├── fish-speech/        # Cloned fishaudio/fish-speech repo (created by setup.sh)
└── venv/               # Python virtual environment (created by setup.sh)
```

## Prerequisites

- **Python 3.10+**
- **Git**
- **NVIDIA GPU** with 12+ GB VRAM (24 GB recommended for S2-Pro)
  - CPU-only mode is supported but significantly slower

## Quick Start

### 1. Run the setup script

```bash
cd fish-audio-s2
./setup.sh
```

This will:
- Clone the [fishaudio/fish-speech](https://github.com/fishaudio/fish-speech) repo
- Create a Python virtual environment
- Install all dependencies
- Download the `openaudio-s1-mini` model weights (~4 GB)

### 2. Start the Fish-Audio API server

```bash
./start_server.sh
# Or with a specific model and port:
./start_server.sh openaudio-s1-mini 8080
```

The TTS API will be available at `http://localhost:8080/v1/tts`.

### 3. Use with the main app

The main FastAPI backend includes a `/tts` endpoint that proxies requests to the Fish-Audio S2 server. Once both servers are running, you can generate speech from the web UI.

## Voice Cloning (Optional)

To use a custom voice, place reference audio in the `references/` directory:

```
references/
└── my-voice/
    ├── sample.wav    # 5-30 seconds of clear speech
    └── sample.lab    # Transcription of the audio
```

Then specify the reference ID when calling the TTS endpoint.

## Emotion & Prosody Control

S2 supports inline tags for expressive speech:

```
[laugh] That's hilarious!
[whispers] Can you hear me?
[super happy] I got the job!
[sad] I'll miss you.
```

## Links

- [Installation docs](https://speech.fish.audio/install/)
- [Inference docs](https://speech.fish.audio/inference/)
- [GitHub repo](https://github.com/fishaudio/fish-speech)
- [Model on HuggingFace](https://huggingface.co/fishaudio/openaudio-s1-mini)
