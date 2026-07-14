# Overlay 적용 방법

`sejong_ai_codex_overlay.zip`은 기존 프로젝트 루트에 덮어쓸 **Codex 지침·문서·계약·스크립트 묶음**이다. 기존 소스코드를 삭제하지 않는다.

## 권장 순서

1. 기존 프로젝트를 Git에 커밋하거나 별도 백업한다.
2. overlay ZIP을 프로젝트 루트에 압축 해제한다.
3. 기존 파일이 `apps/`, `data/`, `contracts/`와 충돌하면 즉시 덮어쓰기보다 diff를 확인한다.
4. 기존 오래된 코드·문서는 `legacy/`로 이동하거나 `docs/02_CURRENT_REPO_AUDIT.md`에 위치를 기록한다.
5. Codex를 저장소 루트에서 열고 `CODEX_START_PROMPT.md`를 첫 메시지로 사용한다.
6. Codex가 발견 감사와 인터뷰를 끝내기 전 제품 코드를 대규모 수정하지 않는다.

## 전체 준비본과의 차이

- overlay: 현재 저장소에 추가할 지침/문서 중심, 기존 프로젝트는 별도로 유지
- full ready project: 업로드 원본을 `legacy/uploaded-project/`에 포함한 새 정리본
