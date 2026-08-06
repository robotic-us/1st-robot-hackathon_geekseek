# CAD 원본

- `Assemble_CAM.step`: `reference/Assemble_CAM.step`에서 가져온 전체 카메라 로봇 어셈블리 원본
- 단위: STEP 원본 기준 mm
- 용도: 실제 링크 메시 분리와 치수 검증을 위한 기준 자료

현재 STEP 어셈블리는 FreeCAD에서 298개 솔리드가 평탄화되어 관절별 이름을 안정적으로 복원하기 어렵다.
첫 RViz 모델은 전체 크기와 6개 액추에이터 구성을 반영한 경량 primitive URDF를 사용한다. 이후 링크별 메시가
확정되면 상태 머신이나 ROS 토픽을 바꾸지 않고 URDF의 `visual`만 CAD 메시로 교체한다.
