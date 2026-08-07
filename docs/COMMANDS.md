# 명령어 모음

## 설치

```bash
python3 -m pip install -e '.[dev]'
```

## 서버 실행

```bash
python3 -m geekseek --config config/<설정파일>
```

| 설정 파일 | 용도 |
|---|---|
| `config/dev.yaml` | 기본 개발용 — robot/capture/person_sensor 전부 fake, http:8000 |
| `config/local-demo-no-robot.yaml` | 웹캠 인식 + iPad UI만, 로봇 없이 — https:8443 |
| `config/local-demo.yaml` | RViz 로봇 포함 전체 로컬 데모 — https:8443 |
| `config/jetson-phorce.yaml` | Jetson 실기 (phorce 로봇 연동) — https:8443 |

접속 주소: `http(s)://<서버 IP>:<port>/face`(iPad1), `/guide`(iPad2), `/debug`. iPad는 서버와 같은
Wi-Fi 대역에 있어야 한다.

`https:8443` 설정은 `certs/`에 인증서가 없으면 시작이 실패한다:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem \
  -days 3650 -nodes -subj "/CN=geekseek"
```

## Jetson(phorce)에서 GPU로 실행

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda run --no-capture-output -n geekseek python -m geekseek --config config/local-demo-no-robot.yaml
```

로그에 `delegate=gpu`가 찍히면 정상. GPU wheel 빌드/환경 구성은
[`mediapipe-gpu-build.md`](mediapipe-gpu-build.md) 참고.

## 테스트

```bash
pytest tests/
```
