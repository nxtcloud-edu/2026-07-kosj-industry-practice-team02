# 구현 노트 운영 규칙

모든 사용자 요청/질문 단위로 구현 노트를 만든다. 코드 변경이 없는 조사·결정·문서 작업도 포함한다.

## 이름

`IMP-YYYYMMDD-NNN-short-slug.md`

## 생성

```bash
python scripts/new_implementation_note.py --title "저장소 감사" --task-id DISC-001 --type discovery
```

## 품질 기준

- 명령과 실제 결과가 있어야 한다.
- 파일 경로·버전 전후·테스트·롤백이 구체적이어야 한다.
- 사실과 가정, 완료와 미완료를 구분한다.
- 처음 보는 사람이 재현할 수 있어야 한다.
- 인간 필수 이해와 AI 내부 세부를 분리한다.

## 완료 조건

노트 파일 생성 + `INDEX.md` 행 추가 + 관련 PLAN/TASK/ADR 링크.
