"""Create a captioned MP4 and voice WAV from Gemini TTS, one scene at a time."""
import json
import os
import subprocess
import sys
import time
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gemini_tts import synthesize_gemini

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'automation' / 'build'
OUT = ROOT / 'automation' / 'outputs'
SIZE = (1080, 1920)

def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                    *map(str, args)], check=True)

def korean_font(size):
    for name in ('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
                 '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
                 'C:/Windows/Fonts/malgunbd.ttf'):
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    raise RuntimeError('한국어 폰트가 설치되어 있지 않습니다.')

def render_caption(text, speaker, dest):
    width, height = SIZE
    im = Image.new('RGB', SIZE, (13, 11, 29))
    d = ImageDraw.Draw(im)
    for y in range(height):
        f = y / height
        d.line((0, y, width, y), fill=(int(22+12*f), int(12+8*f), int(47+14*f)))
    d.rounded_rectangle((52, 72, width-52, 180), radius=28, fill=(51, 39, 81))
    d.text((84, 87), '루사연 | 가족 사연', font=korean_font(52),
           fill=(248, 240, 224))
    is_male = speaker in ('son', 'male')
    d.text((88, 1170), '아들' if is_male else '엄마',
           font=korean_font(54), fill=(242, 198, 117))
    f = korean_font(72)
    words = text.split()
    lines, current = [], ''
    for word in words:
        candidate = word if not current else current + ' ' + word
        if len(candidate) > 16 and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    lines = [chunk for line in lines for chunk in
             textwrap.wrap(line, width=16, break_long_words=True)]
    heights = [d.textbbox((0, 0), line, font=f)[3] for line in lines]
    y = 1380 - (sum(heights) + 22 * (len(lines)-1)) // 2
    for line, h in zip(lines, heights):
        w = d.textbbox((0, 0), line, font=f)[2]
        d.text(((width-w)//2, y), line, font=f, fill='white',
               stroke_width=2, stroke_fill=(45, 36, 54))
        y += h + 22
    d.text((90, 1760), '구독과 좋아요는 큰 힘이 됩니다',
           font=korean_font(42), fill=(184, 170, 208))
    im.save(dest)

def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1
                else ROOT / 'automation' / 'request.json')
    job = json.loads(path.read_text(encoding='utf-8'))
    scenes = job.get('scenes')
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 30:
        raise ValueError('scenes는 1~30개의 대사여야 합니다.')
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    segments, voices = [], []
    for index, scene in enumerate(scenes):
        text = str(scene.get('text', '')).strip()
        speaker = str(scene.get('speaker', 'mother')).lower()
        if not text or len(text) > 600 or speaker not in (
            'mother', 'female', 'narrator', 'son', 'male'
        ):
            raise ValueError(f'{index+1}번 대사 형식이 올바르지 않습니다.')
        voice = 'Charon' if speaker in ('son', 'male') else 'Kore'
        wav = WORK / f'voice_{index:02d}.wav'
        png = WORK / f'caption_{index:02d}.png'
        clip = WORK / f'clip_{index:02d}.mp4'
        # Gemini TTS Tier-1 allows 10 generate requests/minute. Pace calls.
        if index:
            time.sleep(7)
        for attempt in range(3):
            try:
                synthesize_gemini(text, voice, str(wav))
                break
            except Exception as error:
                if '429' not in str(error) or attempt == 2:
                    raise
                print(f'Gemini rate limit: waiting before retry {attempt + 1}', flush=True)
                time.sleep(25)

        render_caption(text, speaker, png)
        ffmpeg('-loop', '1', '-framerate', '24', '-i', png, '-i', wav,
               '-c:v', 'libx264', '-preset', 'ultrafast',
               '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
               '-ar', '24000', '-ac', '1', '-shortest',
               '-movflags', '+faststart', clip)
        segments.append(clip)
        voices.append(wav)
    video_list = WORK / 'video_list.txt'
    video_list.write_text(''.join(f"file '{p.resolve()}'\n" for p in segments))
    ffmpeg('-f', 'concat', '-safe', '0', '-i', video_list,
           '-c', 'copy', OUT / 'ru_sayeon_shorts.mp4')
    audio_list = WORK / 'audio_list.txt'
    audio_list.write_text(''.join(f"file '{p.resolve()}'\n" for p in voices))
    ffmpeg('-f', 'concat', '-safe', '0', '-i', audio_list,
           '-c:a', 'pcm_s16le', OUT / 'ru_sayeon_voice.wav')
    print('Gemini TTS + MP4 completed')

if __name__ == '__main__':
    main()
