const page = document.documentElement.dataset.page;
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const copy = {
  booting: ["시스템을 준비하고 있어요", "잠시만 기다려 주세요."],
  ready: [page === "face" ? "어떤 사진을 찍어볼까요?" : "구도를 선택해 주세요", page === "face" ? "원하는 구도를 선택해 주세요." : "상단 iPad에서 촬영 구도를 골라주세요."],
  repositioning: ["카메라가 이동 중이에요", "로봇과 안전거리를 유지해 주세요."],
  guiding: ["가이드에 맞춰 서주세요", "화면의 실루엣 안으로 천천히 이동해 주세요."],
  verifying: ["구도를 확인하고 있어요", "자세를 잠시 유지해 주세요."],
  capturing: ["촬영 중이에요", "하나, 둘, 셋!"],
  reviewing: ["사진이 완성됐어요", "사진을 선택하거나 다시 촬영할 수 있어요."],
  error: ["확인이 필요해요", "관리자 화면에서 오류를 초기화해 주세요."],
};

async function post(path) {
  const response = await fetch(path, {method: "POST"});
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function update(context) {
  const [headline, message] = copy[context.state] || [context.state, ""];
  if ($("#headline")) $("#headline").textContent = headline;
  if ($("#message")) $("#message").textContent = context.hint || context.error || message;
  if ($("#state")) $("#state").textContent = `${context.state} · r${context.revision}`;
  if ($("#debug-json")) $("#debug-json").textContent = JSON.stringify(context, null, 2);
  document.body.dataset.state = context.state;

  $$('[data-template]').forEach((button) => button.disabled = context.state !== "ready");
  if ($("#align")) $("#align").disabled = context.state !== "guiding";
  if ($("#retake")) $("#retake").disabled = context.state !== "reviewing";
  if ($("#accept")) $("#accept").disabled = context.state !== "reviewing";
  if ($("#reset")) $("#reset").disabled = context.state !== "error";

  const photo = $("#photo");
  if (photo) {
    photo.src = context.photo_url || "";
    photo.hidden = !context.photo_url;
  }
}

function bind(selector, path) {
  const element = $(selector);
  if (!element) return;
  element.addEventListener("click", async () => {
    try { await post(path); } catch (error) { $("#message").textContent = error.message; }
  });
}

$$('[data-template]').forEach((button) => button.addEventListener("click", async () => {
  try { await post(`/api/template/${button.dataset.template}`); }
  catch (error) { $("#message").textContent = error.message; }
}));
bind("#align", "/api/alignment-ready");
bind("#retake", "/api/retake");
bind("#accept", "/api/accept");
bind("#reset", "/api/reset");

const events = new EventSource("/events");
events.addEventListener("open", () => { $("#connection").textContent = "실시간 연결됨"; $("#connection").classList.add("online"); });
events.addEventListener("state", (event) => update(JSON.parse(event.data)));
events.addEventListener("error", () => { $("#connection").textContent = "재연결 중"; $("#connection").classList.remove("online"); });
