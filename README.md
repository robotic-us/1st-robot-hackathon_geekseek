# GeekSeek — 제1회 로봇 해커톤 2026

로보틱어스(Roboticus)가 주최하는 제1회 로봇 해커톤(2026. 8. 5.~8. 8., KAIST) 참가팀 **GeekSeek**(서울대)의 저장소입니다.

- 팀원: 김민재 · 박상원 · 강채은
- 대회: https://robotic-us.com

## 지적재산권

> 본 프로젝트의 지적재산권은 GeekSeek 팀(팀원 전원)에게 있으며, 본 대회의 주최 측(로보틱어스)은 아카이브 및 홍보 목적으로만 본 저장소를 활용합니다.

라이선스는 팀이 선택해 `LICENSE` 파일로 추가하세요(MIT 또는 Apache-2.0 권장).

## 개발 실행

처음 한 번 개발 의존성을 설치한다.

```bash
python3 -m pip install -e '.[dev]'
```

로봇 없이 iPad 웹서버와 상태 머신을 실행한다.

```bash
python3 -m geekseek --config config/dev.yaml
```

같은 컴퓨터에서는 `http://localhost:8000/debug`, iPad에서는 같은 Wi-Fi에 연결한 뒤 아래 주소로 접속한다.

- iPad 1: `http://<서버-IP>:8000/face`
- iPad 2: `http://<서버-IP>:8000/guide`
- 개발 화면: `http://<서버-IP>:8000/debug`

현재 iPad 2의 `개발용: 정렬 완료` 버튼이 실제 Pose의 `ALIGNMENT_STABLE` 이벤트를 대신한다.
카메라/Pose 연결 전에도 구도 선택→fake robot→촬영→리뷰→재촬영/확정 전체 흐름을 확인할 수 있다.

UI 없이 상태 머신만 한 번 실행하려면 `--demo`를 추가한다.

RViz fake robot 실행법은 [`ros/geekseek_fake_robot/README.md`](ros/geekseek_fake_robot/README.md)를
참고한다. 실제 CAD 원본은 `assets/cad/Assemble_CAM.step`에 보존되어 있다.
