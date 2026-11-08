// 샘플 대본 데이터
const SAMPLES = {
  success: {
    title: "성공하는 사람들의 하루 1분 습관",
    script: "성공하는 사람들은 아침에 눈을 뜨자마자 작은 목표 하나를 세웁니다.\n포기하고 싶은 순간이 찾아올 때, '딱 1분만 더 해보자'고 다짐하세요.\n매일 쌓이는 작은 노력이 결국 당신의 인생을 완전히 바꿉니다.\n오늘 당신의 위대한 여정을 지금 바로 시작하세요!"
  },
  health: {
    title: "아침 공복에 마시는 따뜻한 물 한 잔의 기적",
    script: "아침에 일어나자마자 마시는 미온수 한 잔은 밤새 끈적해진 혈액을 맑게 해줍니다.\n장 운동을 활발하게 만들어 소화력을 높이고 체내 독소를 빠르게 배출하죠.\n오늘부터 커피 대신 따뜻한 물 한 잔으로 건강한 하루를 시작해 보세요!"
  },
  curiosity: {
    title: "우리가 몰랐던 뇌의 놀라운 비밀",
    script: "인간의 뇌는 몸무게의 2%에 불과하지만 전체 에너지의 20%를 소비합니다.\n잠을 자는 동안에도 뇌는 하루 동안의 기억을 정리하고 뇌세포의 노폐물을 청소하죠.\n충분한 수면이 가장 강력한 집중력의 비결인 이유입니다!"
  }
};

const form = document.getElementById("generate-form");
const titleInput = document.getElementById("video-title");
const scriptInput = document.getElementById("video-script");
const voiceSelect = document.getElementById("voice-select");
const themeSelect = document.getElementById("theme-select");
const speedSelect = document.getElementById("speed-select");
const submitBtn = document.getElementById("submit-btn");

const progressCard = document.getElementById("progress-card");
const progressStatus = document.getElementById("progress-status");

const placeholderPlayer = document.querySelector(".placeholder-player");
const videoPlayer = document.getElementById("video-player");
const videoActions = document.getElementById("video-actions");
const downloadBtn = document.getElementById("download-btn");

const outputsList = document.getElementById("outputs-list");
const refreshBtn = document.getElementById("refresh-btn");
const toast = document.getElementById("toast");

// 포맷 선택 라디오 버튼 활성화 효과
const formatOptions = document.querySelectorAll(".format-option");
formatOptions.forEach(opt => {
  opt.addEventListener("click", () => {
    formatOptions.forEach(o => o.classList.remove("active"));
    opt.classList.add("active");
  });
});

// 샘플 대본 채우기
function loadSample(key) {
  const sample = SAMPLES[key];
  if (sample) {
    titleInput.value = sample.title;
    scriptInput.value = sample.script;
    showToast(`'${sample.title}' 예시 대본이 입력되었습니다.`);
  }
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
}

// 영상 생성 요청
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const title = titleInput.value.trim();
  const script = scriptInput.value.trim();
  const format = document.querySelector('input[name="format"]:checked').value;
  const voice = voiceSelect.value;
  const theme = themeSelect.value;
  const speed = speedSelect.value;

  if (!script) {
    showToast("대본을 입력해 주세요.");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.querySelector(".btn-text").textContent = "⏳ AI 영상 렌더링 중...";
  progressCard.hidden = false;
  progressStatus.textContent = "AI 음성을 합성하고 자막 영상을 렌더링하고 있습니다. (약 10~20초 소요)";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, script, format, voice, theme, speed })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "영상 생성에 실패했습니다.");
    }

    showToast("🎉 영상이 성공적으로 완성되었습니다!");

    // 비디오 플레이어에 로드
    placeholderPlayer.hidden = true;
    videoPlayer.hidden = false;
    videoPlayer.src = data.video_url;
    videoPlayer.play();

    videoActions.hidden = false;
    downloadBtn.href = data.video_url;
    downloadBtn.download = data.filename;

    loadOutputs();
  } catch (err) {
    showToast(`❌ 오류: ${err.message}`);
    progressStatus.textContent = `제작 실패: ${err.message}`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector(".btn-text").textContent = "🚀 AI 자동 영상 제작 시작하기";
    progressCard.hidden = true;
  }
});

// 제작된 영상 목록 로드
async function loadOutputs() {
  try {
    const res = await fetch("/api/outputs");
    const files = await res.json();

    if (!files.length) {
      outputsList.innerHTML = '<li class="empty-item">아직 제작된 영상이 없습니다.</li>';
      return;
    }

    outputsList.innerHTML = files.map(f => `
      <li class="output-item">
        <span class="output-name" title="${f.name}">🎬 ${f.name} (${f.size})</span>
        <button class="chip-btn" onclick="playVideo('${f.url}', '${f.name}')">재생</button>
      </li>
    `).join("");
  } catch (err) {
    console.error("출력 목록 로드 오류:", err);
  }
}

function playVideo(url, filename) {
  placeholderPlayer.hidden = true;
  videoPlayer.hidden = false;
  videoPlayer.src = url;
  videoPlayer.play();

  videoActions.hidden = false;
  downloadBtn.href = url;
  downloadBtn.download = filename;
}

refreshBtn.addEventListener("click", loadOutputs);

// 초기 로딩
loadOutputs();
