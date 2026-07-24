# 평가·인수인계 가이드

처음 보는 사람은 다음 순서로 확인합니다.

1. [`README.md`](../README.md)
2. [`WEEK3_EVALUATION.md`](../WEEK3_EVALUATION.md)
3. [`docs/test-reports/MVP-001-SAMPLE-20-RESULT.md`](test-reports/MVP-001-SAMPLE-20-RESULT.md)
4. [`docs/03_ARCHITECTURE.md`](03_ARCHITECTURE.md)
5. [`docs/07_SECURITY_PRIVACY.md`](07_SECURITY_PRIVACY.md)
6. [`database/README.md`](../database/README.md)
7. [`versions/manifest.json`](../versions/manifest.json)

## 재현 완료 기준

```text
clone
→ pinned runtime 확인
→ dependency install
→ patched local DB bootstrap
→ migration·rollback·pgTAP
→ approved seed 19/3/10
→ API `/ready=200`
→ Web/API 실행
→ 표본·계약·E2E·비밀 검사
```

환경변수 값, DSN, 질문 원문과 실제 개인정보는 인수인계 자료에 넣지 않습니다. 실패한 검증은
숨기지 않고 명령·종료코드·영향 범위만 기록합니다.

## 후속 작업

public 배포, actual 시민 provider, public 관리자 인증, remote backup과 부하 목표는 별도 승인
대상입니다. local demo actor와 개발 credential을 public 환경으로 복사하지 않습니다.
