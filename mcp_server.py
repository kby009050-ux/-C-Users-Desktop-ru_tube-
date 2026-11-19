"""Private MCP adapter for ru_tube's existing Gemini TTS.

Run locally with: python mcp_server.py
The default STDIO transport never opens a public network port.
For ChatGPT, connect through a supported Secure MCP Tunnel and a permitted
custom MCP plugin. Do NOT expose this server through an unauthenticated
public reverse proxy: calls incur Gemini API charges.
"""
import base64
import importlib.util
import os
import shutil
import subprocess
import uuid
import wave
from pathlib import Path
from typing import Literal

from mcp.server.mcpserver import MCPServer

from gemini_tts import synthesize_gemini

SERVER = MCPServer("RuTube Gemini Korean TTS")
AUDIO_DIR = Path(__file__).resolve().parent / "temp_audio"
SUPPORTED_VOICES = ("Kore", "Charon")
MAX_TEXT_CHARS = 450
MAX_WAV_BYTES = 7 * 1024 * 1024


@SERVER.tool()
def gemini_tts_status() -> dict:
    """Check whether ru_tube has a local Gemini API key and SDK installed.

    This does not make a paid Gemini request and never reveals the key.
    A 'configured' result is NOT proof that billing or synthesis succeeds.
    """
    try:
        sdk_installed = importlib.util.find_spec("google.genai") is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        sdk_installed = False
    return {
        "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        "google_genai_installed": sdk_installed,
        "model": os.getenv("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
        "voices": list(SUPPORTED_VOICES),
        "ready_for_test": bool(os.getenv("GEMINI_API_KEY")) and sdk_installed,
        "note": "Real synthesis has not been tested by this status tool.",
    }


@SERVER.tool()
def create_korean_speech(
    text: str,
    voice: Literal["Kore", "Charon"] = "Kore",
    speed: float = 1.0,
) -> dict:
    """Generate actual Korean speech through ru_tube's paid Gemini TTS API.

    Use for short, user-requested Korean narration or dialogue. Korean voices:
    Kore (female) and Charon (male). Optional speed=1.25 preserves pitch using
    local FFmpeg. Returns WAV as base64 so a connected MCP client can use the
    audio without accessing the user's private filesystem. This tool may incur
    Gemini API usage charges. Never call it merely to check connection status.
    """
    text = text.strip()
    if not text or len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"Text must contain 1 to {MAX_TEXT_CHARS} characters.")
    if voice not in SUPPORTED_VOICES:
        raise ValueError("Voice must be Kore or Charon.")
    if not 0.75 <= speed <= 1.5:
        raise ValueError("Speed must be between 0.75 and 1.50.")
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is not set in the ru_tube process.")
    if speed != 1.0 and not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg must be installed for speeds other than 1.0x.")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output = AUDIO_DIR / f"gemini_mcp_{uuid.uuid4().hex}.wav"
    temp = output.with_name(output.stem + "_speed.wav")
    try:
        synthesize_gemini(text, voice, str(output))
        if speed != 1.0:
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(output), "-filter:a", f"atempo={speed:.3f}",
                    "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(temp),
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            temp.replace(output)

        size = output.stat().st_size
        if size > MAX_WAV_BYTES:
            raise RuntimeError("Audio exceeds the 7 MB MCP response limit.")
        with wave.open(str(output), "rb") as wav:
            seconds = wav.getnframes() / wav.getframerate()
        return {
            "status": "generated",
            "voice": voice,
            "speed": speed,
            "duration_seconds": round(seconds, 3),
            "format": "audio/wav",
            "audio_wav_base64": base64.b64encode(output.read_bytes()).decode("ascii"),
            "saved_path": str(output),
        }
    finally:
        if temp.exists():
            temp.unlink()
        # Output is retained locally in temp_audio for video assembly.


if __name__ == "__main__":
    SERVER.run(transport="stdio")
