"""Check the actual spoken words in a previously generated Gemini TTS file."""
import os
import sys
from pathlib import Path
from google import genai
from google.genai import types

audio = Path(sys.argv[1]).read_bytes()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(api_version="v1beta"))
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=audio, mime_type="audio/wav"),
            "이 파일은 한국어 음성입니다. 실제로 들리는 한국어 발화만 순서대로 정확히 받아써 주세요. "
            "대본에 없는 도입 안내문이나 음성합성 지시가 실제로 들리면 반드시 포함하고, "
            "들은 말 이외에는 설명이나 추측을 넣지 마세요."
        ]
    )
    print("=== ACTUAL SPEECH TRANSCRIPTION ===")
    print(response.text or "[No transcript]")
finally:
    client.close()
