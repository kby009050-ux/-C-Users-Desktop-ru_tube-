let currentVideoUrl = "";

const urlForm = document.getElementById("url-form");
const urlInput = document.getElementById("youtube-url");
const fetchBtn = document.getElementById("fetch-btn");
const previewCard = document.getElementById("preview-card");
const videoThumbnail = document.getElementById("video-thumbnail");
const videoDuration = document.getElementById("video-duration");
const videoTitle = document.getElementById("video-title");
const videoChannel = document.getElementById("video-channel");
const videoViews = document.getElementById("video-views");
const videoDesc = document.getElementById("video-desc");

const dlMp4Btn = document.getElementById("dl-mp4-btn");
const dlMp3Btn = document.getElementById("dl-mp3-btn");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");
const statusText = document.getElementById("status-text");

const refreshFilesBtn = document.getElementById("refresh-files-btn");
const filesList = document.getElementById("files-list");
const toast = document.getElementById("toast");

function showToast(message, duration = 3000) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, duration);
}

// 1. 영상 정보 조회
urlForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  fetchBtn.disabled = true;
  fetchBtn.querySelector(".btn-text").textContent = "정보 불러오는 중...";

  try {
    const res = await fetch("/api/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "영상 정보를 가져올 수 없습니다.");
    }

    currentVideoUrl = url;
    videoThumbnail.src = data.thumbnail;
    videoDuration.textContent = data.duration;
    videoTitle.textContent = data.title;
    videoChannel.textContent = data.channel;
    videoViews.textContent = `조회수 ${data.view_count}회`;
    videoDesc.textContent = data.description;

    previewCard.hidden = false;
    progressContainer.hidden = true;
    showToast("영상을 불러왔습니다! 원하는 다운로드 형식을 선택하세요.");
  } catch (err) {
    showToast(`오류: ${err.message}`);
  } finally {
    fetchBtn.disabled = false;
    fetchBtn.querySelector(".btn-text").textContent = "조회하기";
  }
});

// 2. 다운로드 실행
async function triggerDownload(type) {
  if (!currentVideoUrl) return;

  dlMp4Btn.disabled = true;
  dlMp3Btn.disabled = true;
  progressContainer.hidden = false;
  progressBar.style.width = "40%";
  statusText.textContent = `${type.toUpperCase()} 변환 및 다운로드 중입니다. 잠시만 기다려 주세요...`;

  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: currentVideoUrl, type })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "다운로드에 실패했습니다.");
    }

    progressBar.style.width = "100%";
    statusText.textContent = "다운로드 완료! 파일 저장 중...";
    showToast(`✅ ${data.message}`);

    // 브라우저 파일 다운로드 트리거
    const a = document.createElement("a");
    a.href = data.download_url;
    a.download = data.filename;
    document.body.appendChild(a);
    a.click();
    a.remove();

    // 보관함 목록 갱신
    loadFiles();
  } catch (err) {
    showToast(`❌ ${err.message}`);
    statusText.textContent = `다운로드 실패: ${err.message}`;
  } finally {
    dlMp4Btn.disabled = false;
    dlMp3Btn.disabled = false;
  }
}

dlMp4Btn.addEventListener("click", () => triggerDownload("mp4"));
dlMp3Btn.addEventListener("click", () => triggerDownload("mp3"));

// 3. 파일 보관함 불러오기
async function loadFiles() {
  try {
    const res = await fetch("/api/files");
    const files = await res.json();

    if (!files.length) {
      filesList.innerHTML = '<li class="empty-state">아직 다운로드한 파일이 없습니다.</li>';
      return;
    }

    filesList.innerHTML = files.map(file => `
      <li class="file-item">
        <div class="file-info">
          <span>${file.name.endsWith(".mp3") ? "🎵" : "🎬"}</span>
          <span class="file-name" title="${file.name}">${file.name}</span>
          <span class="file-size">${file.size}</span>
        </div>
        <a href="${file.url}" class="btn btn-secondary btn-sm" download="${file.name}">다운로드</a>
      </li>
    `).join("");
  } catch (err) {
    console.error("파일 목록 로드 실패:", err);
  }
}

refreshFilesBtn.addEventListener("click", loadFiles);

// 초기 로딩 시 보관함 목록 조회
loadFiles();
