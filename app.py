import os
import re
import asyncio
import uuid
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# MoviePy v2.x 호환 임포트
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips
)

app = Flask(__name__)

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
AUDIO_DIR = BASE_DIR / "temp_audio"
BG_DIR = BASE_DIR / "backgrounds"

for d in [OUTPUT_DIR, AUDIO_DIR, BG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 지원 음성 목록
VOICES = {
    "sunhi": {"name": "선희 (친절하고 밝은 여성)", "id": "ko-KR-SunHiNeural"},
    "injoon": {"name": "인준 (차분하고 신뢰감 있는 남성)", "id": "ko-KR-InJoonNeural"},
    "hyunsu": {"name": "현수 (자연스러운 내레이션 남성)", "id": "ko-KR-HyunsuNeural"},
    "jiwan": {"name": "지완 (부드러운 여성)", "id": "ko-KR-JiWanNeural"},
}

def create_gradient_frame(width, height, t, total_t, color_theme="purple"):
    """동적인 감성 그라디언트 배경 생성"""
    ratio = (t / max(total_t, 1)) * 0.5
    if color_theme == "purple":
        r1, g1, b1 = int(25 + ratio * 30), int(10 + ratio * 15), int(45 + ratio * 30)
        r2, g2, b2 = int(10), int(15), int(25)
    elif color_theme == "blue":
        r1, g1, b1 = int(10 + ratio * 20), int(25 + ratio * 30), int(55 + ratio * 35)
        r2, g2, b2 = int(5), int(10), int(20)
    else: # dark/gold
        r1, g1, b1 = int(35 + ratio * 25), int(30 + ratio * 20), int(15 + ratio * 10)
        r2, g2, b2 = int(15), int(15), int(15)

    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        factor = y / height
        arr[y, :, 0] = int(r1 * (1 - factor) + r2 * factor)
        arr[y, :, 1] = int(g1 * (1 - factor) + g2 * factor)
        arr[y, :, 2] = int(b1 * (1 - factor) + b2 * factor)
    return arr

def create_caption_image(text: str, width: int, height: int, is_shorts: bool) -> np.ndarray:
    """한글 자막을 Pillow로 렌더링하여 넘파이 배열 반환"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 기본 폰트 크기 계산
    font_size = int(width * 0.055) if is_shorts else int(width * 0.038)
    
    font = None
    # 윈도우 기본 한글 폰트 탐색 (맑은 고딕 등)
    font_paths = [
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        "C:/Windows/Fonts/arial.ttf"
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                continue

    if font is None:
        font = ImageFont.load_default()

    # 텍스트 줄바꿈 처리
    words = text.split()
    lines = []
    curr = []
    max_chars_per_line = 14 if is_shorts else 24
    
    for w in words:
        curr.append(w)
        if len(" ".join(curr)) >= max_chars_per_line:
            lines.append(" ".join(curr))
            curr = []
    if curr:
        lines.append(" ".join(curr))

    full_text = "\n".join(lines)

    # 텍스트 바운딩 박스 계산
    bbox = draw.textbbox((0, 0), full_text, font=font, align="center")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # 자막 위치 (쇼츠: 중앙 살짝 아래, 롱폼: 화면 하단 20%)
    x = (width - tw) // 2
    y = int(height * 0.68) if is_shorts else int(height * 0.78)

    # 자막 배경 박스 (반투명 어두운 라운드 박스)
    pad_x = 30
    pad_y = 18
    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + tw + pad_x, y + th + pad_y],
        radius=18,
        fill=(0, 0, 0, 190)
    )

    # 텍스트 그림자
    shadow_offset = 2
    draw.text((x + shadow_offset, y + shadow_offset), full_text, font=font, fill=(0, 0, 0, 255), align="center")
    # 텍스트 본문 (하이라이트 옐로우/화이트)
    draw.text((x, y), full_text, font=font, fill=(255, 235, 59, 255), align="center")

    return np.array(img)

async def generate_speech(text: str, voice_id: str, output_path: str, rate: str = "+0%"):
    """Edge-TTS를 이용한 한국어 고품질 음성 합성"""
    communicate = edge_tts.Communicate(text, voice_id, rate=rate)
    await communicate.save(output_path)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/voices", methods=["GET"])
def get_voices():
    return jsonify(VOICES)

@app.route("/api/generate", methods=["POST"])
def generate_video():
    data = request.get_json() or {}
    title = data.get("title", "자동화 영상").strip()
    script = data.get("script", "").strip()
    format_type = data.get("format", "shorts") # 'shorts' (9:16) 또는 'longform' (16:9)
    voice_key = data.get("voice", "sunhi")
    theme = data.get("theme", "purple")
    speed = data.get("speed", "+0%")

    if not script:
        return jsonify({"error": "영상 대본(스크립트)을 입력해 주세요."}), 400

    job_id = uuid.uuid4().hex[:8]
    audio_path = str(AUDIO_DIR / f"{job_id}.mp3")
    output_filename = f"{re.sub(r'[\\/*?:\x22<>|]', '', title)}_{format_type}_{job_id}.mp4"
    output_path = str(OUTPUT_DIR / output_filename)

    voice_id = VOICES.get(voice_key, VOICES["sunhi"])["id"]

    try:
        # 1. 음성 합성 (Edge-TTS)
        asyncio.run(generate_speech(script, voice_id, audio_path, rate=speed))
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        # 2. 해상도 설정
        if format_type == "shorts":
            width, height = 1080, 1920 # 9:16 세로
            is_shorts = True
        else:
            width, height = 1920, 1080 # 16:9 가로
            is_shorts = False

        # 3. 배경 영상 생성 (동적 애니메이션 그라디언트)
        def make_bg_frame(t):
            return create_gradient_frame(width, height, t, duration, theme)

        from moviepy import VideoClip
        bg_clip = VideoClip(make_bg_frame, duration=duration)

        # 4. 자막 클립 생성 (대본을 문장 단위로 분할하여 타이밍 맞춤)
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', script) if s.strip()]
        if not sentences:
            sentences = [script]

        sentence_duration = duration / len(sentences)
        caption_clips = []

        for i, sentence in enumerate(sentences):
            start_t = i * sentence_duration
            end_t = min((i + 1) * sentence_duration, duration)
            clip_dur = end_t - start_t

            cap_img = create_caption_image(sentence, width, height, is_shorts)
            cap_clip = (
                ImageClip(cap_img)
                .with_start(start_t)
                .with_duration(clip_dur)
            )
            caption_clips.append(cap_clip)

        # 5. 영상 합성 (배경 + 자막 + 오디오)
        final_video = CompositeVideoClip([bg_clip] + caption_clips, size=(width, height))
        final_video = final_video.with_audio(audio_clip)

        # 6. 최종 렌더링
        final_video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger=None
        )

        # 자원 정리
        audio_clip.close()
        final_video.close()
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({
            "success": True,
            "filename": output_filename,
            "title": title,
            "duration": round(duration, 1),
            "video_url": f"/outputs/{output_filename}"
        })

    except Exception as e:
        return jsonify({"error": f"영상 제작 실패: {str(e)}"}), 500

@app.route("/api/outputs", methods=["GET"])
def list_outputs():
    files = []
    for p in OUTPUT_DIR.iterdir():
        if p.is_file() and p.suffix.lower() == ".mp4":
            size_mb = round(p.stat().st_size / (1024 * 1024), 2)
            files.append({
                "name": p.name,
                "size": f"{size_mb} MB",
                "created": p.stat().st_mtime,
                "url": f"/outputs/{p.name}"
            })
    files.sort(key=lambda x: x["created"], reverse=True)
    return jsonify(files)

@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=False)

if __name__ == "__main__":
    print("=" * 60)
    print("🎬 ru_tube AI 쇼츠 & 롱폼 자동 제작 스튜디오")
    print("👉 브라우저 주소: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
