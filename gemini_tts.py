"""Gemini TTS adapter for ru_tube. Never commit the GEMINI_API_KEY secret."""
import os
import wave
from pathlib import Path


def synthesize_gemini(text: str, voice: str, output_path: str, style: str = ''):
    """Write a Gemini-generated WAV file. Supports WAV or 24kHz PCM output."""
    from google import genai
    from google.genai import types

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 환경변수를 먼저 설정하세요.")
    if voice not in ("Kore", "Charon", "Sola"):
        raise ValueError("지원 음성: Kore, Charon, Sola")

    # SDK 3.x defaults to v1; Gemini TTS speechConfig requires v1beta.
    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(api_version="v1beta"),
    )
    try:
        result = client.models.generate_content(
            model=os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
            contents=types.Content(role='user', parts=[types.Part(text=text, speech_metadata=types.SpeechMetadata(style=style))]) if style else text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    )
                ),
            ),
        )
    finally:
        client.close()

    parts = result.candidates[0].content.parts if result.candidates else []
    audio = next((p.inline_data for p in parts if getattr(p, "inline_data", None)), None)
    if not audio or not audio.data:
        raise RuntimeError("Gemini에서 음성 데이터가 반환되지 않았습니다.")
    mime = (audio.mime_type or "").lower()
    data = audio.data
    if isinstance(data, str):
        import base64
        data = base64.b64decode(data)
    if mime in ("audio/wav", "audio/x-wav", "audio/wave") or data[:4] == b"RIFF":
        Path(output_path).write_bytes(data)
    elif "audio/l16" in mime or "audio/pcm" in mime:
        with wave.open(str(Path(output_path)), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(data)
    else:
        raise RuntimeError("예상하지 못한 오디오 형식: " + mime)
