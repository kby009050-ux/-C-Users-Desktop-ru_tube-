# 루사연 OpenAI TTS 사용법

기존 Gemini / Edge-TTS 기능을 변경하지 않는 독립형 OpenAI TTS 모듈입니다.

1. `pip install openai`
2. OpenAI Platform에서 API 키 발급 (ChatGPT 구독과 API 결제는 별개)
3. Windows PowerShell에서 현재 세션에만 키 설정: `$env:OPENAI_API_KEY="발급받은키"`
4. `python openai_tts.py --text "강아지는 오늘도 그 자리를 떠나지 않았습니다." --output output/narration.mp3 --voice nova`

생성된 MP3를 기존 영상 제작 파이프라인에 불러와 사용하세요. **영상 렌더러와 자동 연결은 아직 하지 않았습니다.**

보안: API 키를 GitHub 파일, README, 커밋 또는 영상에 절대 넣지 마세요. 이 저장소는 공개 저장소입니다.

참고: OpenAI 음성은 Gemini Nika/Riko와 동일한 목소리가 아닙니다. 자막 동기화는 별도 타임스탬프 처리가 필요합니다.
