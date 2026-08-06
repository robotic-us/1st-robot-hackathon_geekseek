(() => {
  "use strict";

  const page = document.documentElement.dataset.page;
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
    "여러 구도로 버스트 촬영",
    "촬영 결과 빠른 미리보기",
    "반응과 선택을 기다리는 중",
    "사진 전달 후 인사",
  ];
  const faceMoods = [
    ["mood-gentle", "상냥한 기본 얼굴", "반가워요"],
    ["mood-sparkly", "초롱초롱 웃는 얼굴", "두 분, 너무 잘 어울려요"],
    ["mood-sparkly", "웃으며 기다리는 얼굴", "어떤 사진이 좋을까요?"],
    ["mood-excited", "약간 신나하는 얼굴", "좋아요, 시작해볼까요?"],
    ["mood-wink", "촬영할 때마다 윙크하는 얼굴", "찰칵 · 01"],
    ["mood-curious", "결과가 궁금한 얼굴", "어떻게 나왔을까요?"],
    ["mood-waiting", "반응을 기다리는 얼굴", "마음에 드시나요?"],
    ["mood-happy", "밝게 웃으며 인사하는 얼굴", "다음에 또 만나요"],
  ];

  let stage = 1;
  let stageTimer = null;
  let effectTimer = null;
  let effectTimeout = null;
  let carouselIndex = 0;
  let burstCount = 1;
  let slideIndex = 0;

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];

  function clearEffects() {
    window.clearInterval(stageTimer);
    window.clearInterval(effectTimer);
    window.clearTimeout(effectTimeout);
    stageTimer = null;
    effectTimer = null;
    effectTimeout = null;
    document.body.classList.remove("wave-mode");
  }

  function setStage(nextStage) {
    clearEffects();
    stage = ((nextStage - 1 + 8) % 8) + 1;
    const url = new URL(window.location.href);
    url.searchParams.set("stage", String(stage));
    window.history.replaceState(null, "", url);
    $("#stage-label").textContent = `SCENE ${String(stage).padStart(2, "0")}`;
    $("#caption").textContent = captions[stage - 1];

    const next = $("#next-stage");
    if (next) next.innerHTML = stage === 8 ? "처음으로 <span>↻</span>" : "다음 단계 <span>→</span>";

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

    if (stage === 5) {
      let shot = 1;
      const wink = () => {
        shot = shot >= 100 ? 1 : shot + 1;
        $("#face-note").textContent = `찰칵 · ${String(shot).padStart(2, "0")}`;
        face.classList.add("wink-now");
        effectTimeout = window.setTimeout(() => face.classList.remove("wink-now"), 230);
      };
      wink();
      effectTimer = window.setInterval(wink, 680);
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
    if (stage === 5) startBurst();
    if (stage === 6) startSlideshow();
    if (stage === 7 || stage === 8) drawQrCodes();
  }

  function updateCarousel() {
    const strip = $("#example-strip");
    if (!strip) return;
    strip.style.transform = `translateX(-${carouselIndex * 100}%)`;
    $("#carousel-count").textContent = `${carouselIndex + 1} / 3`;
    $$(".carousel-dots i").forEach((dot, index) => dot.classList.toggle("active", index === carouselIndex));
  }

  function startBurst() {
    burstCount = 1;
    const poses = ["UPPER BODY", "FULL BODY", "WIDE ANGLE", "CLOSE UP"];
    const update = () => {
      burstCount = burstCount >= 100 ? 1 : burstCount + 1;
      $("#burst-count").textContent = `촬영 중 · ${String(burstCount).padStart(2, "0")} / 100`;
      $("#burst-progress").style.width = `${burstCount}%`;
      $("#pose-name").textContent = poses[Math.floor((burstCount - 1) / 25)];
    };
    update();
    effectTimer = window.setInterval(update, 82);
  }

  function startSlideshow() {
    slideIndex = 0;
    const shots = $$(".saved-shot");
    const film = $$(".film-strip i");
    const update = () => {
      shots.forEach((shot, index) => shot.classList.toggle("active", index === slideIndex));
      film.forEach((dot, index) => dot.classList.toggle("active", index === slideIndex));
      $("#slide-count").textContent = `${String(slideIndex + 1).padStart(2, "0")} / ${String(shots.length).padStart(2, "0")}`;
      slideIndex = (slideIndex + 1) % shots.length;
    };
    update();
    effectTimer = window.setInterval(update, 360);
  }

  function drawQrCodes() {
    $$(".qr-canvas").forEach((canvas) => drawQr(canvas));
  }

  function drawQr(canvas) {
    const context = canvas.getContext("2d");
    const modules = 29;
    const quiet = 3;
    const total = modules + quiet * 2;
    const unit = canvas.width / total;
    const reserved = new Set();
    context.fillStyle = "#f7f8ff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#101522";

    const cell = (x, y) => context.fillRect((x + quiet) * unit, (y + quiet) * unit, Math.ceil(unit), Math.ceil(unit));
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

  $("#next-stage")?.addEventListener("click", () => setStage(stage + 1));
  $("#prev-stage")?.addEventListener("click", () => setStage(stage - 1));
  $("#carousel-prev")?.addEventListener("click", () => { carouselIndex = (carouselIndex + 2) % 3; updateCarousel(); });
  $("#carousel-next")?.addEventListener("click", () => { carouselIndex = (carouselIndex + 1) % 3; updateCarousel(); });
  $("#start-capture")?.addEventListener("click", () => setStage(4));
  $("#decline")?.addEventListener("click", () => setStage(1));
  $("#review-again")?.addEventListener("click", () => setStage(6));
  $("#review-like")?.addEventListener("click", () => setStage(8));

  const requestedStage = Number(new URLSearchParams(window.location.search).get("stage"));
  setStage(Number.isInteger(requestedStage) && requestedStage >= 1 && requestedStage <= 8 ? requestedStage : 1);
})();
