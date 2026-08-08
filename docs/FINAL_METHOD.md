# 최종 방식 — 측정에서 손님 폰까지

손교시 없이 촬영 궤적을 만들고, 그 궤적을 도는 동안 사진을 찍어, 손님 폰으로
넘기기까지의 전체 방식. 실기에서 확인한 제약과 아직 확인 못 한 것을 함께 적는다.

```
관절각 측정        → calibration/trial_02.csv
   ↓ 순서 최적화 + P-Vector 생성
SD카드 슬롯 4·5    → PCM이 재생 (28초)
   ↓ 시간 스케줄대로 셔터
사진 40장          → photos/
   ↓ 세션 토큰 + QR
손님 폰            → 갤러리에서 전부 저장
```

## 1. 왜 손교시를 안 하나

참가자 코드가 로봇에 할 수 있는 일은 `/phorce/feedback` 읽기와
`play(슬롯 1~50)` 두 가지뿐이다. 실시간 제어가 없으니 촬영 구도는 **미리 SD카드에
적재된 모션**이어야 한다.

phorce Studio의 정식 절차는 서보를 끄고 팔을 손으로 움직여 녹화하는 것이지만,
카메라 구도는 손으로 재현할 수 있는 정밀도가 아니다. 대신 P-Vector
`[yd, Ltraj, s0, sd]`를 코드로 계산해 `MotionMap.csv`에 직접 쓴다. 끝점 각도만
주면 그 사이는 5차 다항식이 채우고, **각 구간 시작·끝 속도가 항상 0**이라
웨이포인트마다 팔이 정확히 멈춘다 — 그 정지가 곧 촬영 타이밍이 된다.

## 2. 실물 MotionMap 포맷 (교육자료와 다름)

`file_version 3.0.0` 기준. SD카드의 `Motions/motion_01.csv`를 직접 읽어 확인했다.

```
robot_id,1
file_version,3.0.0
MS ID,MS Name,MD ID,P vector
,,,0,1,2,...,19                     ← P-Vector 컬럼은 20개 (10개 아님)
4,PHOTO_FULLBODY,MD0,"-0.9,600,0,0","-0.9,3140,0,0",...
,,MD3,-,-,...                       ← 안 쓰는 축은 "-"
```

| 항목 | 실물 | 비고 |
|---|---|---|
| P-Vector 개수 | **20** | PDF/PPTX 예시의 10개는 구버전 |
| `C-Vector` 컬럼 | **없음** | PPTX에만 있음 |
| MD 번호 | **축 인덱스와 동일** | MD0/1/2/6/8 ↔ `known_mask=327` |
| `yd` 단위 | degree, 소수점 1자리 | 절대 목표각 (상대 변위 아님) |
| `Ltraj` | 1kHz 틱 | |
| **한 MS 내 모든 MD의 `Ltraj` 합** | **정확히 같아야 함** | 축 동기화의 근거 |
| `memo.json`의 `motion_sha256` | CSV 바이트의 실제 SHA-256 | 3개 슬롯 전부 일치 확인 |

`memo.json`에 박힌 영점(`zero_offset_f32_le_hex`)이 `config/pose-zero-offsets.json`과
**0.0005 rad(0.03°) 이내로 일치**한다. 그래서 측정한 각도를 부호·스케일 변환 없이
`yd`에 그대로 넣을 수 있다.

## 3. 슬롯 만들기

```bash
python3 scripts/build_motion_slots.py                 # calibration/slots/ 에 생성
python3 scripts/build_motion_slots.py --out /media/phorce/<SD>/Motions
```

하는 일:

1. `trial_02.csv`에서 웨이포인트를 읽는다 (전신 8개, 상반신 9개)
2. **방문 순서를 전수탐색으로 최적화** — 홈에서 출발해 전부 들르고 홈 복귀,
   관절공간 이동량 최소. 전신 99.3°→64.6°(35%↓), 상반신 305.4°→239.4°(22%↓)
3. 총 28초를 배분한다. 이동 시간은 거리÷속도로 정하고, **남는 시간은 전부 정지에**
   몰아준다 — 남는 시간을 이동 속도 늦추는 데 쓰면 포즈 잡을 시간이 안 생긴다
4. 5개 MD가 **동일한 Ltraj 시퀀스**를 쓰게 해서 합계 일치 제약을 자동 충족
5. `motion_NN.csv` + `memo.json` + `memo.json.pending` + `schedule.json` 생성

결과:

| | 웨이포인트 | P-Vector | 정지 | 총 |
|---|---|---|---|---|
| 슬롯 4 전신 | 8 | 17/20 | 2.89초 | 28.00초 |
| 슬롯 5 상반신 | 9 | 19/20 | 1.80초 | 28.00초 |

### 왜 30초가 아니라 28초인가

`phorce play`의 기본 대기 시간이 **정확히 30.0초**다(`phorce/cli.py`, Python
파사드의 `handle.wait(timeout=30.0)`도 동일). 30초짜리 모션은 물리적으로 완주하고도
결과가 `timeout - cancel 요청`으로 떨어진다. 실제로 겪었다.

### SD에 쓴 뒤

**언마운트하고 PCM 전원을 껐다 켜야** 반영된다. Jetson이 카드를 USB 저장장치로
물고 있는 동안 PCM은 그 카드를 못 읽는다. 반영 확인은 `phorce_monitor` 기동 로그:

```
적재 슬롯 마스크 0x000000000000003E   ← 0b111110 = 슬롯 1,2,3,4,5
```

슬롯 1~3만 있으면 `0x0E`다.

## 4. 재생과 촬영

`src/geekseek/robot.py`의 `PhorceRobot`.

### 발사 전 검증 (`preflight`)

기동 시 1회, 팔은 움직이지 않는다.

```
doctor()   → duplicate_action_server 확인 → report.ok 확인
motions.list() → 로봇이 실제 적재한 슬롯에 4·5가 있는지
```

카탈로그 정본은 **로봇(PCM)이 적재한 슬롯**이지 Jetson의 파일이 아니다. 실패해도
웹서버는 뜬다 — 스택을 아직 안 올렸을 뿐일 수 있고, 그때 서버까지 죽으면 원인을
볼 화면이 없다. 대신 stderr로 경고를 찍는다.

### 발사 (`_fire`)

```
_wait_until_idle()  → contract_active → is_fresh → boot_id≠0 → state_name=="IDLE"
play_async(slot)    → 시계 시작
_confirm_accepted() → 유예 1.5초 안에 terminal에 도달했으면 "거절"
```

**결과를 기다리는 것과 수락을 확인하는 것은 다르다.** 거절된 goal은 결과가 즉시
세팅되고, 수락된 goal은 28초 내내 pending이다. "아직 결과가 없다"를 성공으로
읽으면, 거절된 팔 앞에서 40장을 찍고 28초 뒤에야 실패를 알게 된다.

재시도는 **코드 5(BUSY)에서만** 한다. 12(NOT_READY)·13(RECOVERY_REQUIRED)은
사람이 버튼을 눌러야 하고 기다려도 안 풀린다. abort 후 자동 재전송도 하지 않는다 —
매뉴얼이 "로봇이 완전히 멈춘 것을 눈으로 확인한 뒤에만"이라고 못박는다.

### 완료 판정

`handle.wait()`가 예외 없이 반환해도 성공이 아니다. CANCELED는 예외가 아니라
결과로 돌아온다. `PlayResult.ok`(SUCCEEDED + `physical_idle` +
`active_request_id == request_id` + `not recovery_required` 등 8개 조건)를 본다.

### 셔터 타이밍

액션 피드백의 `pvector_index`는 **전송 진행이지 재생 진행이 아니다**(SDK 주석이
명시). 그래서 진행률로 쓸 수 없다. 대신 `Ltraj`를 우리가 정했으니 정지 구간이
언제인지 밀리초 단위로 이미 안다 — **발사 시각 기준 시간 스케줄**로 쏜다.

- 정지 구간 **정중앙에 보장샷** (웨이포인트 개수만큼 반드시)
- 남는 예산은 정지 구간 → 이동 구간 순으로 채움
- **최대 2Hz** (폰 브릿지 검증 범위). 창을 넘나드는 간격까지 전역으로 검사한다
- 셔터가 늦어 0.35초 이상 밀린 컷은 **버린다**. 몰아서 쏘면 레이트 상한이 무너지고,
  어차피 이동 중에 찍혀 의도한 구도가 아니다. 보장샷은 절대 안 버린다

### 연속 운전

큐가 없다 — 앞 모션이 정착하기 전에 보낸 요청은 유예되지 않고 버려진다. 그래서
매 발사 전에 IDLE을 확인하고, **과열 자동 차단이 없으므로**(매뉴얼 §10) 재생
사이에 쿨다운을 둔다(기본 5초).

## 5. 사진과 갤러리

### 해상도

`getUserMedia`에 제약이 없으면 480×640급 스트림이 온다 — 기념사진으로 못 쓴다.
반대로 센서 원본은 장당 2~3MB라 40장이면 100MB가 넘어 회선이 못 버틴다.

**긴 변 1440px, 세로 3:4 고정.** 해상도 제약은 힌트일 뿐이라 카메라가 16:9 같은
native 모드로 응답할 수 있으므로, 스트림 비율을 믿지 않고 **캔버스에서 3:4로
잘라낸다**. 구도(웨이포인트 각도)를 3:4 기준으로 잡았기 때문에 비율이 바뀌면
프레이밍이 통째로 달라진다.

### 왜 별도 포트인가

키오스크는 자체서명 인증서를 쓴다. 우리가 직접 세팅한 촬영용 폰에는 괜찮지만,
QR을 찍은 손님에게는 "이 연결은 비공개가 아닙니다" 화면이 이탈 지점이 된다.

갤러리는 별도 포트(기본 8080)에 평문 HTTP로 뜨고, **Tailscale Funnel**이 그것을
Let's Encrypt 인증서가 붙은 공개 주소로 내보낸다.

```bash
sudo tailscale funnel --bg 8080
tailscale funnel status        # 여기 나오는 https 주소를 gallery_base_url에
```

신뢰된 origin은 경고를 없애는 것 이상의 값이 있다 — `navigator.share`는 secure
context에서만 존재하고, 그게 **한 벌을 개별 이미지로 사진첩에 넣는 유일한 경로**다.
공개 주소라 손님이 Wi-Fi를 갈아탈 필요도 없다(셀룰러로 접속).

### 저장 경로가 플랫폼마다 다르다

| | 통로 | 결과 |
|---|---|---|
| iOS | `navigator.share({files})` | 공유시트 "이미지 N개 저장" → **사진 앱** |
| 안드로이드 | `<a download>` 반복 | Downloads → 갤러리 앱 **"Download" 앨범** |
| 그 외 | 길게 눌러 저장 | |

**기능 감지로는 못 가른다.** 두 플랫폼 다 두 API를 지원하는데 결과가 다르다.
안드로이드 공유시트에는 "저장" 항목이 없어서 `share`를 쓰면 "다른 앱으로 보내기"
목록만 뜬다. 그래서 플랫폼으로 분기한다.

iOS 경로는 파일을 **버튼이 눌리기 전에** 준비해 둔다 — 클릭 후에 받아오면 사용자
활성화가 만료돼 iOS가 거부한다. 안드로이드는 URL로 바로 받으므로 대기가 없다.

### 세션 분리

촬영 건마다 추측 불가능한 토큰(`secrets.token_urlsafe`)을 발급한다. `photos/`를
통째로 노출하면 앞 손님 사진까지 같이 보인다. 최근 200세션만 들고 있다.

## 6. 실행

```bash
# 터미널 1 — 로봇 전원을 먼저 켠 뒤. axes는 5 (SDK 문서 예시의 2는 벤치용)
source /opt/ros/humble/setup.bash
ros2 run agx_phorce_bridge phorce_monitor \
  --ros-args -p nic:=eno1 -p mode:=command -p axes:=5 -p mbx_enabled:=true

# 터미널 2
ros2 run agx_motion_slot motion_action_server --ros-args -p backend:=ecat

# 터미널 3
python3 -m geekseek --config config/jetson-phorce.yaml
```

기동 로그에서 확인할 것:

```
[geekseek] gallery: https://<...>.ts.net (local :8080)      ← 있어야 함
[geekseek] 로봇 사전 검증 실패 — ...                          ← 없어야 함
```

`preflight`는 기동 시 1회만 돈다. 스택을 나중에 올렸다면 geekseek을 재시작해야
한다.

## 7. 검증 상태

**확인됨**

- 코드로 만든 슬롯을 PCM이 받아들임 (슬롯 마스크 `0x0E`→`0x3E`, `phorce list` 5개)
- 슬롯 4 실기 재생 성공, 홈(전 축 0°) 복귀 확인
- 속도가 손교시 모션보다 전 축에서 보수적 (최대 25 vs 49.7 deg/s)
- QR이 실제로 스캔됨 — 화면 스크린샷을 디코딩해 URL 일치 확인
- Funnel 공개 주소가 외부망에서 열림, Let's Encrypt 인증서
- 안드로이드 다운로드·iOS 공유·길게누르기 폴백 3경로 실제 브라우저 검증

**미확인 — 실기에서 재야 함**

- `accept_grace_seconds = 1.5` — goal 수락 왕복 실측값 없음
- **발사 → 실제 팔 움직임 시작 지연.** 촬영 시계는 발사 직후부터 돈다. 상반신 첫
  보장샷 여유가 ±0.9초뿐이라 여기가 가장 빡빡하다
- **iOS 공유시트의 파일 개수 한계.** 문서화된 값이 없다. 40장이 막히면
  `photo_target_count`를 낮추거나 배치로 나눈다

앞의 두 개는 슬롯 4를 한 번 재생하면서 `/phorce/feedback`을 1kHz로 기록해
예정 정지 구간과 실제 정지 시각을 겹쳐보면 한 번에 나온다.

## 8. 안전

- 발사한 모션은 코드로 멈출 수 없다. **정지 수단은 E-Stop 물리 버튼 하나뿐**이다
- `cancel()`은 E-Stop이 아니다
- 슬롯 5는 시작 2.5초 안에 MD6이 61.7° 접힌다. 첫 실기 확인은 진입 이동이 10°
  이내인 **슬롯 4부터** 하는 게 안전하다
- 과열 자동 차단이 없다 — 쉼 없는 반복 재생 금지

## 참고

- `docs/COMMANDS.md` — 명령어 모음
- `context/knowledge/decisions.md` — 확정 사항
- `context/knowledge/reference/sdk-docs/` — SDK 원문
