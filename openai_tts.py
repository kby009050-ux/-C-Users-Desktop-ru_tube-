"""OpenAI TTS for ru_tube Studio. Requires OPENAI_API_KEY in environment."""
import argparse
import os
from pathlib import Path
from openai import OpenAI

VOICES = ("alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer")

def synthesize(text: str, output: str, voice: str = "nova") -> Path:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    if voice not in VOICES:
        raise ValueError(f"지원하지 않는 목소리: {voice}")
    if not text.strip():
        raise ValueError("대본이 비어 있습니다.")
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    ) as response:
        response.stream_to_file(target)
    return target

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="루사연 OpenAI 한국어 TTS")
    parser.add_argument("--text", required=True, help="읽을 한국어 대본")
    parser.add_argument("--output", default="output/narration.mp3")
    parser.add_argument("--voice", choices=VOICES, default="nova")
    args = parser.parse_args()
    print(synthesize(args.text, args.output, args.voice))
