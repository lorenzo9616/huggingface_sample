"""
Lightweight Python client for the Fish-Audio S2 /v1/tts endpoint.

Usage:
    from fish_audio_s2.fish_audio_client import FishAudioClient

    client = FishAudioClient()              # defaults to localhost:8080
    audio_bytes = client.tts("Hello!")      # returns raw audio bytes
    client.tts_to_file("Hello!", "out.wav") # writes to file
"""

import urllib.request
import urllib.error
import json
import base64
import os


class FishAudioClient:
    """Client for the Fish-Audio S2 local API server."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")

    def tts(
        self,
        text: str,
        reference_audio_path: str | None = None,
        reference_text: str | None = None,
        reference_id: str | None = None,
    ) -> bytes:
        """
        Convert text to speech via the Fish-Audio S2 API.

        Args:
            text: The text to synthesise.
            reference_audio_path: Path to a .wav file for voice cloning.
            reference_text: Transcript of the reference audio.
            reference_id: Pre-registered reference voice ID.

        Returns:
            Raw audio bytes (WAV/PCM).
        """
        payload: dict = {"text": text}

        if reference_id:
            payload["reference_id"] = reference_id

        if reference_audio_path and os.path.isfile(reference_audio_path):
            with open(reference_audio_path, "rb") as f:
                payload["reference_audio"] = base64.b64encode(f.read()).decode()
            if reference_text:
                payload["reference_text"] = reference_text

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.base_url}/v1/tts",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise RuntimeError(
                f"Fish-Audio S2 API error {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ConnectionError(
                f"Cannot reach Fish-Audio S2 at {self.base_url}. "
                "Is the server running? (./start_server.sh)"
            ) from exc

    def tts_to_file(
        self,
        text: str,
        output_path: str,
        reference_audio_path: str | None = None,
        reference_text: str | None = None,
        reference_id: str | None = None,
    ) -> str:
        """Generate speech and write it to a file. Returns the output path."""
        audio = self.tts(
            text,
            reference_audio_path=reference_audio_path,
            reference_text=reference_text,
            reference_id=reference_id,
        )
        with open(output_path, "wb") as f:
            f.write(audio)
        return output_path

    def health(self) -> bool:
        """Return True if the Fish-Audio S2 server is reachable."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/", method="GET"
            )
            with urllib.request.urlopen(req, timeout=5):
                return True
        except Exception:
            return False
