# 트랙 D — 키오스크 웹서버 뼈대

## 목표
Jetson에 로컬 웹서버(FastAPI 권장)를 띄우고, iPad 2대가 각자 지정된 페이지를 Safari
풀스크린(가이드 접근 모드)으로 표시하는 것까지 확인한다. 네이티브 iOS 앱은 만들지 않는다
(`../../knowledge/decisions.md` 확정 사항).

## 왜 지금 이걸 해두면 좋은가
현장 Wi-Fi/기기 조합에서 막히는 지점(방화벽, mDNS, 핫스팟 격리 등)은 실제로 붙여보기 전엔 모른다.
뼈대만 먼저 세워두면 B(스켈레톤 오버레이)·C(캡처 브릿지) 결과물을 나중에 라우트 몇 개만 추가해서
꽂을 수 있다.

## 현재 상태
`진행 중 · FastAPI/SSE/iPad 1·2 화면 구현 완료`

구현된 경로:

- `/face`: 구도 3종 선택과 현재 상태 표시
- `/guide`: 가이드 placeholder, 개발용 정렬 완료, fake 사진 리뷰·재촬영·확정
- `/debug`: 전체 컨텍스트와 모든 개발용 제어
- `/events`: `WorkflowContext` SSE 실시간 전송

노트북의 실제 Uvicorn/API/SSE 왕복은 검증했다. 실제 iPad 2대의 Safari 접속과 MJPEG 영상 연결은 남아 있다.

## 다음 단계
1. ~~FastAPI 최소 서버와 상태 API 구현.~~
2. ~~라우트 2개로 분리:~~
   - `/face` (iPad1용) — 얼굴/상태 표시 + 구도 템플릿 썸네일 선택 UI. 상태는 SSE/WebSocket으로 push.
   - `/guide` (iPad2용) — 라이브 프리뷰(처음엔 그냥 원본 웹캠 스트림, 나중에 B트랙 합성 오버레이로 교체)
     + 모드 선택/재촬영 버튼(터치 → `POST`).
3. Jetson·iPad를 같은 Wi-Fi(또는 Jetson 핫스팟)에 붙이고, iPad Safari에서 `http://<Jetson IP>:<port>/face`,
   `/guide` 접속 확인 → 설정 앱에서 "가이드 접근 모드"로 풀스크린 고정.
4. ~~SSE 상태 push를 브라우저/API 테스트로 확인.~~ 실제 iPad 2대 동시 접속을 추가 확인.
5. B트랙이 완성되면 `/guide`의 프리뷰 소스를 원본 웹캠 → B트랙의 합성 프레임(MJPEG)으로 교체.
   C트랙이 완성되면 캡처 결과 미리보기를 `/guide`에 표시.

## 완료 기준
- 두 iPad가 각자 `/face`, `/guide`를 풀스크린으로 표시.
- Jetson에서 보낸 상태 변경이 폴링 없이 실시간으로 화면에 반영됨.
- 현장 네트워크 조건(핫스팟/공유기)에서 접속 테스트를 최소 1회 완료.

## 참고
- `../../knowledge/architecture/camera-robot-architecture.html` §2(iPad↔Jetson 연동), §3(시스템 다이어그램의 "키오스크 서버")

## 진행 기록
"현재 상태"를 바꿀 정도의 진전이 있으면 `../../progress/log/`에 날짜별로 한 줄 남기고,
`../../progress/STATUS.md`의 이 트랙 행도 같이 갱신하세요. 세부 메모는 이 폴더의 `NOTES.md`에.
