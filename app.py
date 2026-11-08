import os
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)

# 다운로드 디렉토리 설정
DOWNLOAD_DIR = Path(__file__).resolve().parent / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(name: str) -> str:
    """안전한 파일명으로 변환"""
    return re.sub(r'[\\/*?:"<>|]', "", name)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/info", methods=["POST"])
def get_video_info():
    data = request.get_json() or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "유튜브 링크를 입력해 주세요."}), 400

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            duration_sec = info.get("duration", 0)
            minutes, seconds = divmod(duration_sec, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"

            return jsonify({
                "title": info.get("title", "제목 없음"),
                "thumbnail": info.get("thumbnail", ""),
                "channel": info.get("uploader", info.get("channel", "알 수 없음")),
                "duration": duration_str,
                "view_count": f"{info.get('view_count', 0):,}",
                "description": (info.get("description") or "")[:200] + "...",
                "url": url
            })
    except Exception as e:
        return jsonify({"error": f"영상 정보를 불러오지 못했습니다: {str(e)}"}), 500

@app.route("/api/download", methods=["POST"])
def download_video():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    download_type = data.get("type", "mp4").lower() # 'mp4' 또는 'mp3'

    if not url:
        return jsonify({"error": "유튜브 링크를 입력해 주세요."}), 400

    out_tmpl = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    if download_type == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_tmpl,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
        }
    else:
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_tmpl,
            "quiet": True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_type == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
            
            basename = os.path.basename(filename)
            return jsonify({
                "success": True,
                "message": "다운로드가 성공적으로 완료되었습니다!",
                "filename": basename,
                "download_url": f"/downloads/{basename}"
            })
    except Exception as e:
        return jsonify({"error": f"다운로드 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route("/api/files", methods=["GET"])
def list_files():
    files = []
    for p in DOWNLOAD_DIR.iterdir():
        if p.is_file():
            size_mb = round(p.stat().st_size / (1024 * 1024), 2)
            files.append({
                "name": p.name,
                "size": f"{size_mb} MB",
                "created": p.stat().st_mtime,
                "url": f"/downloads/{p.name}"
            })
    files.sort(key=lambda x: x["created"], reverse=True)
    return jsonify(files)

@app.route("/downloads/<path:filename>")
def serve_download(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 ru_tube 서버가 실행되었습니다!")
    print("👉 브라우저 주소: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
