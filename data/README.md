# data/ — 데이터 규칙

> 상세 규칙 정리 중 (3주차 업데이트 예정)

- 이 폴더의 JSON이 유일한 원본이며, DB 적재본과 엑셀 스냅샷은 산출물이다.
- 커밋 전 `python data/scripts/validate.py` 실행 필수.
- `exports/`(엑셀 스냅샷)와 비밀 값은 커밋하지 않는다.