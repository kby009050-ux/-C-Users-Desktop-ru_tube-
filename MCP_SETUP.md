# 루튜브 Gemini TTS MCP 연결

기존 `gemini_tts.py`를 호출하는 **개인용 MCP 서버**입니다. API 키는 GitHub에 올리지 않고, 루튜브가 실행되는 **컴퓨터의 GEMINI_API_KEY 환경 변수**만 사용합니다.

## 구현된 도구

- `gemini_tts_status`: API 키 설정 여부, SDK 설치 여부를 확인합니다. Gemini 호출이나 과금은 일어나지 않습니다. 실제 정상 연결 여부를 보장하지는 않습니다.
- `create_korean_speech`: 한국어 대사를 Gemini TTS로 WAV 음성으로 생성합니다. `voice="Kore"`(여성), `voice="Charon"`(남성), `speed=1.25` 지원. 결과는 로컬 `temp_audio/`에 저장하고 MCP 응답으로 WAV의 base64 데이터를 전달합니다. **실제 생성 요청은 Gemini API 이용 요금이 발생할 수 있습니다.**

이 코드는 ChatGPT에 자동 설치되지 않습니다. 서버 코드 생성과 플러그인 연결은 별도 단계입니다.

## 1. 기존 PC에 코드를 가져오고 필요한 패키지 설치

Windows에서 루튜브 프로젝트 폴더를 열고 최신 GitHub 변경사항을 가져오세요.

```bat
git pull origin main
venv\Scripts\python.exe -m pip install -r requirements.txt
```

기존 `GEMINI_API_KEY`가 같은 PC에서 설정되어 있는지만 **값을 노출하지 않고** 확인합니다.

```bat
venv\Scripts\python.exe -c "import os; print('설정됨' if os.getenv('GEMINI_API_KEY') else '설정 안 됨')"
```

`설정됨`이면 키를 다시 발급할 필요가 없습니다. 실제 API 호출 성공 여부는 별도 테스트가 필요합니다.

## 2. MCP 실행

`run_mcp.bat`는 로컬 STDIO 방식의 MCP 서버를 실행합니다. 다른 프로그램(MCP 클라이언트/터널)이 실행하며 통신하는 형태입니다. 직접 더블클릭하면 별도 화면 없이 기다리는 것이 정상입니다.

```bat
run_mcp.bat
```

서버는 기본적으로 네트워크 포트를 열지 않습니다. **유료 Gemini API를 호출할 수 있으므로 이 서버를 인증 없이 인터넷에 공개하지 마세요.**

## 3. ChatGPT에 연결(지원되는 계정/워크스페이스에서만)

현재 OpenAI 공식 도움말 기준 전체 사용자 정의 MCP 도구의 생성/호출은 주로 ChatGPT Business 및 Enterprise/Edu의 허용된 워크스페이스에서 지원됩니다. **개인 Plus에서 이 개인 MCP의 음성 생성 도구를 직접 호출할 수 있다고 가정하면 안 됩니다.** 사용자 본인 계정에서 'Add custom MCP server' 메뉴 유무를 확인하세요.

원격 연결은 **Secure MCP Tunnel**을 우선 권장합니다. 이 기능은 OpenAI Platform 조직의 터널 권한과 별도의 런타임 인증 구성이 필요합니다.

1. [OpenAI Platform Secure MCP Tunnel 설명](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)을 참고하여, 사용할 수 있는 조직에서 Tunnel을 만듭니다.
2. 본인 PC에 `tunnel-client`를 설치하고, 위의 로컬 STDIO MCP 서버를 호출하도록 프로필을 구성합니다. 로컬 `run_mcp.bat`의 **실제 절대경로**를 명령으로 전달합니다. 터널 ID·런타임 키는 본인 PC에만 안전하게 보관하세요.
3. `tunnel-client doctor`로 연결을 확인하고 `tunnel-client run`을 실행합니다.
4. [ChatGPT Plugins](https://chatgpt.com/plugins) → + → Add custom MCP server → Connection: Tunnel에서 해당 터널을 선택합니다.
5. 플러그인을 설치한 뒤 `gemini_tts_status`를 먼저 호출하고, 문제없으면 **짧은 대사**로 `create_korean_speech`를 테스트합니다.

개인 컴퓨터/터널이 켜져 있어야 호출할 수 있습니다. 이 저장소에 파일이 생겼다는 것만으로 이 채팅에서 바로 호출되는 것은 아닙니다.

## 음성 샘플

- text: `엄마 장례식을 마친 날, 죽은 엄마에게 전화가 왔습니다.`
- voice: `Kore`
- speed: `1.25`

현재 루튜브 `app.py`는 화면에서 한 번에 한 음성만 고르는 구조입니다. **등장인물별 자동 음성 분리와 애니 사진 합성 기능은 이 MCP 추가만으로 구현되지 않습니다.**
