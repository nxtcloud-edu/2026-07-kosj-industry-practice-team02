# MVP-001 표본 20 deterministic 평가 결과

- 실행일: 2026-07-23 KST
- 입력 권위: `data/evaluation/sample_questions_20.csv`
- 범위: exact ID `T-01`~`T-20`
- 명령: `pytest apps/api/tests/chat/test_sample_questions_20.py`
- 결과: **21 passed, 0 skipped** — 20개 case + exact-matrix meta test 1개

## 결과

| 판정 | 결과 |
|---|---:|
| 전체 | 20/20 |
| SUCCESS grounded-record outcome | 10/10 |
| FOLLOWUP | 2/2 |
| FALLBACK | 8/8 |
| └ INSUFFICIENT_GROUNDING | 2/2 |
| └ PERSONAL_LOOKUP | 2/2 |
| └ LEGAL_JUDGMENT | 2/2 |
| └ OUT_OF_SCOPE | 2/2 |

T-16은 보수적 마스킹과 정책 outcome 경계를 포함해 통과했다. 이 결과는 결정론적 pure-service
평가이며 DeepSeek/provider 품질, remote/public 운영, 실제 시민 정확도 또는 HTTP source-card 화면
QA를 증명하지 않는다. HTTP·DB 실제 개선 루프 근거는 MVP-001 구현 노트와 별도 local lineage가
소유한다.
