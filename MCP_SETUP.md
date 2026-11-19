# 루튜브 → ChatGPT: 생성된 Gemini TTS 음성 가져오기

이 MCP는 **음성을 생성하지 않습니다.** 루튜브에서 이미 생성한 음성 파일을 ChatGPT 등의 MCP 클라이언트가 가져오기 위한 **읽기 전용 연결**입니다.

## 현재 루튜브 코드 동작
1. 루튜브 앱에서 Gemini TTS를 선택해 영상을 생성하면 기존 GEMINI_API_KEY를 사용해 목소리를 합성합니다.
2. `app.py`는 생성된 음성 `temp_audio/<작업번호>.wav`를 더 이상 삭제하지 않고 보관합니다.
3. `mcp_server.py`는 다음 두 가지 도구만 제공합니다:
   - `list_generated_audio`: 생성된 음성 파일 목록을 조회
   - `get_generated_audio`: 목록에 있는 파일 하나를 Base64 오디오로 가져오기
4. MCP를 통해 **새로 음성을 만들거나 Gemini API를 호출하지 않습니다.** 기존에 생성되어 삭제된 음성 파일은 되살릴 수 없습니다.

음성 파일은 사적인 작업물일 수 있어 `temp_audio/` 폴더는 GitHub 커밋에서 제외됩니다.

## PC에 반영하기
루튜브 프로젝트 폴더에서:

```bat
git pull origin main
venv\Scripts\python.exe -m pip install -r requirements.txt
```

루튜브를 재시작하고 새 음성 샘플을 생성합니다. 그러면 `temp_audio` 폴더에 WAV 파일이 남아야 합니다.

## MCP 서버
```bat
run_mcp.bat
```

이 배치파일은 로컬 STDIO MCP 서버를 실행합니다. 연결 가능한 MCP 클라이언트가 해당 파일을 실행하도록 설정해야 합니다. 이 명령만 실행해서 ChatGPT 연결이 자동으로 끝나는 것은 아닙니다.

## 이 ChatGPT에서 사용할 수 있는지
[OpenAI 공식 도움말](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt)에 따르면, 사용자 정의 MCP 서버 연결은 ChatGPT Business/Enterprise/Edu의 지원되는 웹 환경에서 제공됩니다. 개인 Plus 계정에서는 **이 MCP를 설치하고 채팅에서 직접 호출할 수 있다고 가정할 수 없습니다.**

지원 계정/조직에서는 인증된 원격 서버 또는 Secure MCP Tunnel을 별도로 구성하고 ChatGPT 사용자 정의 MCP 연결을 해야 합니다. 로컬 STDIO 서버를 인증 없이 공개 인터넷에 노출하면 안 됩니다.

개인 Plus에서 음성을 직접 전달하려면, 루튜브가 만든 `temp_audio` WAV 파일을 이 대화에 첨부하거나, 연결 가능한 외부 저장소 앱에 저장해야 합니다. GitHub 연결만으로 컴퓨터의 로컬 파일을 이 채팅에서 읽을 수는 없습니다.

## 중요
이 MCP 변경은 **파일 가져오기 기능만** 구현했습니다. 영상 생성/자막 동기화/사진 장면 구성은 별도 기능입니다. 아직 PC에서 실행 테스트하거나 이 ChatGPT에 연결 완료한 상태는 아닙니다.
