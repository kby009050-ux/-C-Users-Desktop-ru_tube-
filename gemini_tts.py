"""Gemini TTS adapter for ru_tube. Keep API keys in environment variables."""
import os
import wave
from pathlib import Path

def synthesize_gemini(text: str, voice: str, output_path: str):
    """Create a 24 kHz mono PCM WAV with Gemini TTS."""
    from google import genai
    from google.genai import types
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 환경변수를 먼저 설정하세요.")
    if voice not in ("Kore", "Charon"):
        raise ValueError("지원 음성: Kore, Charon")
    client = genai.Client(api_key=key)
    result = client.models.generate_content(
        model=os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"),
        contents="다음 한국어 대사를 자연스럽게 읽어주세요. 대사 외의 내용은 말하지 마세요.\n\n" + text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )
    parts = result.candidates[0].content.parts if result.candidates else []
    audio = next((p.inline_data for p in parts if getattr(p, "inline_data", None)), None)
    if not audio or not audio.data:
        raise RuntimeError("Gemini에서 음성 데이터가 반환되지 않았습니다.")
    mime = audio.mime_type or ""
    if "audio/l16" not in mime and "audio/pcm" not in mime:
        raise RuntimeError("예상하지 못한 오디오 형식: " + mime)
    with wave.open(str(Path(output_path)), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(audio.data)
