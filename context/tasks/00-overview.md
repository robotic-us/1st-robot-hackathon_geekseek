# 지금 할 일 — 4개 트랙

물리 구성이 정리된 뒤 나온 병렬 작업 목록입니다(`architecture/camera-robot-architecture.html` §11과 동일).
네 트랙은 서로 거의 안 겹치므로 사람/에이전트가 나뉘어 있으면 동시에 시작해도 됩니다. 굳이 순서를
매기면 **A → C → D → B** 순으로 우선순위가 높습니다(A가 안 되면 나머지는 실물에서 의미가 없고, C는
일정 리스크가 가장 큼).

| 트랙 | 파일 | 한 줄 목표 | 로봇 필요? |
|---|---|---|---|
| A | [A-robot-motion-loop.md](A-robot-motion-loop.md) | 모션 슬롯 3~4개 교시 + `play()` 왕복 확인 | 필요 (sim으로 먼저 가능) |
| B | [B-perception-skeleton.md](B-perception-skeleton.md) | C270 → 스켈레톤 → 구도 정렬 점수 | 불필요 — 지금 바로 시작 가능 |
| C | [C-eef-camera-shutter.md](C-eef-camera-shutter.md) | 엔드이펙터 폰 원격 셔터 왕복 확인 | 폰만 있으면 됨 |
| D | [D-kiosk-web-server.md](D-kiosk-web-server.md) | 로컬 웹서버 + iPad Safari 풀스크린 연결 | iPad만 있으면 됨 |

각 트랙 파일은 그 트랙만 보고도 작업을 시작할 수 있도록 목표·근거·현재 상태·다음 단계·완료 기준을
담고 있습니다. 진행하면서 "현재 상태"와 "다음 단계"를 그때그때 업데이트해서, 누가(사람이든 다른
에이전트든) 이어받아도 어디까지 됐는지 바로 알 수 있게 유지하세요.

결정된 것/열려 있는 것은 [`../decisions.md`](../decisions.md)에서 확인하세요.
