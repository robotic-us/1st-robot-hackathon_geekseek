(() => {
  "use strict";

  const page = document.documentElement.dataset.page;
  const debugMode = new URLSearchParams(window.location.search).get("debug") === "1";
  const stateToStage = {
    waiting: 1,
    greeting: 2,
    deciding: 3,
    guiding: 4,
    capturing: 5,
    previewing: 6,
    asking: 7,
    farewell: 8,
  };
  const captions = [
    "안녕하세요! 사진 한 장 찍고 가세요.",
    "두 분 너무 잘 어울리세요. 인생샷 찍어드릴게요!",
    "제가 멋있는 구도로 찍어드릴게요.",
    "화면에 표시된 곳으로 움직여주세요.",
    "여러 개 찍겠습니다. 자연스럽게 포즈를 취해주세요!",
    "짜잔, 이렇게 나왔어요!",
    "마음에 드시나요?",
    "즐거운 시간 되셨길 바라요. 안녕히 가세요!",
  ];
  const stageTitles = [
    "사람을 기다리는 중",
    "가까이 온 사람을 발견",
    "촬영 여부와 구도 선택",
    "촬영 위치 안내",
    "세 가지 구도로 촬영",
    "촬영 결과 빠른 미리보기",
    "반응과 선택을 기다리는 중",
    "사진 전달 후 인사",
  ];
  const faceMoods = [
    ["mood-gentle", "상냥한 기본 얼굴", "반가워요"],
    ["mood-sparkly", "초롱초롱 웃는 얼굴", "두 분, 너무 잘 어울려요"],
    ["mood-sparkly", "웃으며 기다리는 얼굴", "어떤 사진이 좋을까요?"],
    ["mood-excited", "약간 신나하는 얼굴", "좋아요, 시작해볼까요?"],
    ["mood-wink", "촬영할 때마다 윙크하는 얼굴", "촬영 준비 중"],
    ["mood-curious", "결과가 궁금한 얼굴", "어떻게 나왔을까요?"],
    ["mood-waiting", "반응을 기다리는 얼굴", "마음에 드시나요?"],
    ["mood-happy", "밝게 웃으며 인사하는 얼굴", "다음에 또 만나요"],
  ];
  const templateOrder = ["full_body", "upper_body", "product_closeup"];

  let stage = 1;
  let workflowState = "booting";
  let context = {state: "booting", template_id: null, photos: [], hint: "", error: "", revision: 0};
  let stageTimer = null;
  let effectTimer = null;
  let effectTimeout = null;
  let carouselIndex = 0;
  let slideIndex = 0;
  let actionPending = false;

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];

  document.body.classList.toggle("debug-mode", debugMode);

  function clearEffects() {
    window.clearInterval(stageTimer);
    window.clearInterval(effectTimer);
    window.clearTimeout(effectTimeout);
    stageTimer = null;
    effectTimer = null;
    effectTimeout = null;
    document.body.classList.remove("wave-mode");
  }

  function setConnectionChip(mode) {
    const chip = $(".stage-chip");
    const label = $("#stage-label");
    if (!chip || !label) return;
    chip.classList.remove("online", "reconnecting", "workflow-failed");
    if (mode === "booting") label.textContent = "연결 중";
    if (mode === "reconnecting") {
      chip.classList.add("reconnecting");
      label.textContent = "재연결 중";
    }
    if (mode === "error") {
      chip.classList.add("workflow-failed");
      label.textContent = "오류 발생";
    }
    if (mode === "online") {
      chip.classList.add("online");
      label.textContent = `SCENE ${String(stage).padStart(2, "0")}`;
    }
  }

  function enterStage(nextStage) {
    clearEffects();
    stage = nextStage;
    $("#caption").textContent = captions[stage - 1];
    if (page === "face") renderFace();
    if (page === "guide") renderGuide();
  }

  function renderFace() {
    const [mood, label, note] = faceMoods[stage - 1];
    const face = $("#face");
    face.className = `robot-face ${mood}`;
    face.setAttribute("aria-label", label);
    $("#face-note").textContent = note;
    $("#stage-title").textContent = stageTitles[stage - 1];

    if (stage === 1) {
      const wave = () => {
        document.body.classList.add("wave-mode");
        effectTimeout = window.setTimeout(() => document.body.classList.remove("wave-mode"), 2600);
      };
      effectTimeout = window.setTimeout(wave, 900);
      stageTimer = window.setInterval(wave, 10000);
    }

    if (stage === 8) {
      const wave = () => {
        document.body.classList.add("wave-mode");
        effectTimeout = window.setTimeout(() => document.body.classList.remove("wave-mode"), 2500);
      };
      wave();
      stageTimer = window.setInterval(wave, 5500);
    }
  }

  function renderGuide() {
    $$(".guide-scene").forEach((scene) => {
      scene.hidden = Number(scene.dataset.scene) !== stage;
    });
    $$(".stage-progress i").forEach((dot, index) => dot.classList.toggle("active", index === stage - 1));

    if (stage === 1) {
      const wave = () => {
        $(".scene-billboard")?.classList.add("wave-mode");
        effectTimeout = window.setTimeout(() => $(".scene-billboard")?.classList.remove("wave-mode"), 2500);
      };
      effectTimeout = window.setTimeout(wave, 900);
      stageTimer = window.setInterval(wave, 10000);
    }

    if (stage === 3) updateCarousel();
    if (stage === 6) {
      syncSlideshowPhotos();
      startSlideshow();
    }
    if (stage === 7 || stage === 8) drawQrCodes();
  }

  function updateCarousel() {
    const strip = $("#example-strip");
    if (!strip) return;
    strip.style.transform = `translateX(-${carouselIndex * 100}%)`;
    $("#carousel-count").textContent = `${carouselIndex + 1} / ${templateOrder.length}`;
    $$(".carousel-dots i").forEach((dot, index) => dot.classList.toggle("active", index === carouselIndex));
  }

  function selectedTemplate() {
    const cards = $$(".example-card");
    return cards[carouselIndex]?.dataset.template || context.template_id || "full_body";
  }

  function updateCaptureData(previous) {
    const count = context.photos.length;
    const burstCount = $("#burst-count");
    const progress = $("#burst-progress");
    const photoName = $("#pose-name");
    if (burstCount) burstCount.textContent = `촬영 중 · ${count} / 3`;
    if (progress) progress.style.width = `${Math.min(count / 3, 1) * 100}%`;
    if (photoName) photoName.textContent = `PHOTO ${count} / 3`;

    if (page === "face" && workflowState === "capturing") {
      $("#face-note").textContent = count ? `찰칵 · ${String(count).padStart(2, "0")} / 03` : "촬영 준비 중";
      if (count > previous.photos.length) {
        const face = $("#face");
        window.clearTimeout(effectTimeout);
        face.classList.remove("wink-now");
        window.requestAnimationFrame(() => face.classList.add("wink-now"));
        effectTimeout = window.setTimeout(() => face.classList.remove("wink-now"), 300);
      }
    }
  }

  function syncSlideshowPhotos() {
    const frame = $("#slideshow-frame");
    const film = $("#film-strip");
    if (!frame || !film) return;
    const signature = context.photos.join("\n");
    if (frame.dataset.signature === signature) return;
    frame.dataset.signature = signature;
    frame.replaceChildren();
    film.replaceChildren();
    slideIndex = 0;

    if (!context.photos.length) {
      const empty = document.createElement("div");
      empty.className = "slideshow-empty";
      empty.textContent = "사진을 불러오는 중이에요";
      frame.append(empty);
      $("#slide-count").textContent = "00 / 00";
      film.style.gridTemplateColumns = "1fr";
      return;
    }

    context.photos.forEach((photoUrl, index) => {
      const shot = document.createElement("figure");
      shot.className = `saved-shot${index === 0 ? " active" : ""}`;
      const image = document.createElement("img");
      image.src = photoUrl;
      image.alt = `촬영 결과 ${index + 1}`;
      const label = document.createElement("span");
      label.textContent = `PHOTO · ${String(index + 1).padStart(2, "0")}`;
      shot.append(image, label);
      frame.append(shot);
      const dot = document.createElement("i");
      dot.classList.toggle("active", index === 0);
      film.append(dot);
    });
    film.style.gridTemplateColumns = `repeat(${context.photos.length}, 1fr)`;
    updateSlide();
  }

  function updateSlide() {
    const shots = $$("#slideshow-frame .saved-shot");
    const film = $$("#film-strip i");
    if (!shots.length) return;
    if (slideIndex >= shots.length) slideIndex = 0;
    shots.forEach((shot, index) => shot.classList.toggle("active", index === slideIndex));
    film.forEach((dot, index) => dot.classList.toggle("active", index === slideIndex));
    $("#slide-count").textContent = `${String(slideIndex + 1).padStart(2, "0")} / ${String(shots.length).padStart(2, "0")}`;
  }

  function startSlideshow() {
    updateSlide();
    effectTimer = window.setInterval(() => {
      const count = $$("#slideshow-frame .saved-shot").length;
      if (!count) return;
      slideIndex = (slideIndex + 1) % count;
      updateSlide();
    }, 360);
  }

  function updateData(previous) {
    if (workflowState === "capturing") updateCaptureData(previous);
    if (workflowState === "previewing" && page === "guide") syncSlideshowPhotos();
  }

  function ensureFeedback() {
    let feedback = $("#action-feedback");
    if (!feedback) {
      feedback = document.createElement("div");
      feedback.id = "action-feedback";
      feedback.className = "action-feedback";
      feedback.setAttribute("role", "status");
      document.body.append(feedback);
    }
    return feedback;
  }

  function showActionError(message) {
    const feedback = ensureFeedback();
    feedback.textContent = message;
    feedback.classList.add("visible");
    window.setTimeout(() => feedback.classList.remove("visible"), 3200);
  }

  function ensureErrorOverlay() {
    let overlay = $("#workflow-error");
    if (overlay) return overlay;
    overlay = document.createElement("section");
    overlay.id = "workflow-error";
    overlay.className = "workflow-error";
    overlay.hidden = true;
    overlay.innerHTML = '<div><span>!</span><p class="eyebrow">SYSTEM PAUSED</p><h2>잠시 문제가 생겼어요</h2><p id="workflow-error-message"></p><button id="error-reset" type="button">다시 시작</button></div>';
    document.body.append(overlay);
    $("#error-reset").addEventListener("click", () => runAction("/api/reset"));
    return overlay;
  }

  function updateErrorOverlay() {
    const overlay = ensureErrorOverlay();
    const failed = workflowState === "error";
    overlay.hidden = !failed;
    if (failed) $("#workflow-error-message").textContent = context.error || "알 수 없는 오류가 발생했습니다.";
  }

  function updateControls() {
    const deciding = workflowState === "deciding";
    const asking = workflowState === "asking";
    $("#start-capture")?.toggleAttribute("disabled", !deciding || actionPending);
    $("#decline")?.toggleAttribute("disabled", !deciding || actionPending);
    $("#review-again")?.toggleAttribute("disabled", !asking || actionPending);
    $("#review-like")?.toggleAttribute("disabled", !asking || actionPending);

    const next = $("#next-stage");
    if (!next) return;
    const enabled = deciding || asking || workflowState === "error";
    next.disabled = !enabled || actionPending;
    if (deciding) next.innerHTML = '촬영 시작 <span>→</span>';
    else if (asking) next.innerHTML = '마음에 들어요 <span>♥</span>';
    else if (workflowState === "error") next.innerHTML = '다시 시작 <span>↻</span>';
    else next.innerHTML = '자동 진행 대기 중 <span>·</span>';
  }

  async function post(path, body) {
    const options = {method: "POST"};
    if (body !== undefined) {
      options.headers = {"Content-Type": "application/json"};
      options.body = JSON.stringify(body);
    }
    const response = await fetch(path, options);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `요청에 실패했습니다. (HTTP ${response.status})`);
    }
    if (response.status === 204) return null;
    return response.json().catch(() => null);
  }

  async function runAction(path, body) {
    if (actionPending) return;
    actionPending = true;
    updateControls();
    try {
      await post(path, body);
    } catch (error) {
      showActionError(error.message);
    } finally {
      actionPending = false;
      updateControls();
    }
  }

  function runDebugAction() {
    if (workflowState === "deciding") runAction("/api/capture-started", {template_id: selectedTemplate()});
    if (workflowState === "asking") runAction("/api/liked");
    if (workflowState === "error") runAction("/api/reset");
  }

  function applySnapshot(snapshot) {
    if (!snapshot || typeof snapshot.state !== "string") return;
    const previous = context;
    const next = {
      state: snapshot.state,
      template_id: snapshot.template_id ?? null,
      photos: Array.isArray(snapshot.photos) ? snapshot.photos : [],
      hint: snapshot.hint || "",
      error: snapshot.error || "",
      revision: Number.isFinite(snapshot.revision) ? snapshot.revision : 0,
    };
    const stateChanged = next.state !== workflowState;
    context = next;
    workflowState = next.state;

    if (stateToStage[workflowState]) {
      if (stateChanged) {
        if (workflowState === "deciding" && context.template_id && templateOrder.includes(context.template_id)) {
          carouselIndex = templateOrder.indexOf(context.template_id);
        }
        enterStage(stateToStage[workflowState]);
      }
      updateData(previous);
      setConnectionChip("online");
    } else if (workflowState === "booting") {
      if (stage !== 1) enterStage(1);
      setConnectionChip("booting");
    } else if (workflowState === "error") {
      setConnectionChip("error");
    }
    updateErrorOverlay();
    updateControls();
  }

  function drawQrCodes() {
    $$(".qr-canvas").forEach((canvas) => drawQr(canvas));
  }

  function drawQr(canvas) {
    const drawing = canvas.getContext("2d");
    const modules = 29;
    const quiet = 3;
    const unit = canvas.width / (modules + quiet * 2);
    const reserved = new Set();
    drawing.fillStyle = "#f7f8ff";
    drawing.fillRect(0, 0, canvas.width, canvas.height);
    drawing.fillStyle = "#101522";
    const cell = (x, y) => drawing.fillRect((x + quiet) * unit, (y + quiet) * unit, Math.ceil(unit), Math.ceil(unit));
    const finder = (startX, startY) => {
      for (let y = 0; y < 7; y += 1) {
        for (let x = 0; x < 7; x += 1) {
          reserved.add(`${startX + x},${startY + y}`);
          if (x === 0 || x === 6 || y === 0 || y === 6 || (x >= 2 && x <= 4 && y >= 2 && y <= 4)) cell(startX + x, startY + y);
        }
      }
    };
    finder(0, 0); finder(modules - 7, 0); finder(0, modules - 7);
    for (let y = 0; y < modules; y += 1) {
      for (let x = 0; x < modules; x += 1) {
        if (reserved.has(`${x},${y}`)) continue;
        const pattern = (x * 17 + y * 31 + x * y * 3 + (x ^ y) * 7) % 11;
        if (pattern < 5 && !((x < 8 && y < 8) || (x > modules - 9 && y < 8) || (x < 8 && y > modules - 9))) cell(x, y);
      }
    }
  }

  $("#carousel-prev")?.addEventListener("click", () => { carouselIndex = (carouselIndex + 2) % 3; updateCarousel(); });
  $("#carousel-next")?.addEventListener("click", () => { carouselIndex = (carouselIndex + 1) % 3; updateCarousel(); });
  $("#start-capture")?.addEventListener("click", () => runAction("/api/capture-started", {template_id: selectedTemplate()}));
  $("#decline")?.addEventListener("click", () => runAction("/api/decline"));
  $("#review-again")?.addEventListener("click", () => runAction("/api/replay"));
  $("#review-like")?.addEventListener("click", () => runAction("/api/liked"));
  $("#next-stage")?.addEventListener("click", runDebugAction);

  enterStage(1);
  updateCaptureData(context);
  updateErrorOverlay();
  updateControls();
  setConnectionChip("booting");

  const events = new EventSource("/events");
  events.addEventListener("state", (event) => {
    try {
      applySnapshot(JSON.parse(event.data));
    } catch (error) {
      showActionError(`상태 데이터를 읽지 못했습니다: ${error.message}`);
    }
  });
  events.addEventListener("error", () => setConnectionChip("reconnecting"));
})();
