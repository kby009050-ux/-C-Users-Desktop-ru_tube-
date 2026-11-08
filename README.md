# ru_tube - 유튜브 & 음악 다운로더

YouTube 영상(MP4) 및 고음질 음원(MP3)을 쉽고 빠르게 다운로드하고 관리할 수 있는 모던 웹 애플리케이션입니다.

![ru_tube banner](https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80)

---

## ✨ 주요 기능
- 🎬 **YouTube 영상 다운로드**: 원하는 해상도(최고 화질 1080p, 720p 등)로 MP4 다운로드
- 🎵 **음원 추출 (MP3)**: 영상에서 고음질 오디오만 추출하여 MP3 파일로 저장
- 🖼️ **실시간 미리보기**: 링크 입력 즉시 썸네일, 제목, 재생시간, 채널명 확인
- 📂 **다운로드 보관함**: 다운로드한 파일들을 웹에서 바로 재생하거나 관리
- 💻 **원클릭 실행**: `run.bat` 더블클릭만으로 간편 실행 지원

---

## 🚀 빠른 시작 가이드 (Windows)

### 방법 1. 원클릭 실행 (가장 추천)
폴더에 있는 **`run.bat`** 파일을 더블클릭하면 필요한 패키지가 자동 설치되고 웹 브라우저가 실행됩니다.

### 방법 2. 터미널 수동 실행
```bash
# 1. 의존성 패키지 설치
pip install -r requirements.txt

# 2. 서버 실행
python app.py
```
실행 후 브라우저에서 `http://127.0.0.1:5000` 으로 접속하세요.

---

## 🛠️ 기술 스택
- **Backend**: Python 3, Flask, yt-dlp
- **Frontend**: HTML5, Vanilla JavaScript, Modern Responsive CSS (Glassmorphism & Dark Mode)

---

## 📄 라이선스
MIT License
