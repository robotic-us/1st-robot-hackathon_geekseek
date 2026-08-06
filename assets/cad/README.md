# CAD 원본

- `Assemble_CAM.step`: `reference/Assemble_CAM.step`에서 가져온 전체 카메라 로봇 어셈블리 원본
- 단위: STEP 원본 기준 mm
- 용도: 실제 링크 메시 분리와 치수 검증을 위한 기준 자료

FreeCAD의 일반 import에서는 298개 솔리드로 평탄화되지만, OCP XCAF로 읽으면 원래 조립 트리와 부품명이
유지된다. `tools/extract_step_links.py`는 `joints v54`의 5개 `phact-401` 축을 기준으로 고정측(`holder_f`)과
출력측(`holder_m`)을 분리해 6개 링크 STL을 만들고, 최상위의 키오스크 프레임·iPad·C270도 고정 STL로
추출한다. 생성물은 `ros/geekseek_fake_robot/meshes/`에 커밋한다.

STEP AP214에는 URDF 관절 제약이 직접 들어 있지 않다. 따라서 회전축은 액추에이터의 원통 중심·방향과
인접 홀더 형상으로 추론했으며, 실제 로봇의 모션 슬롯/관절 방향과 대조하기 전까지 시뮬레이션 기준값이다.
