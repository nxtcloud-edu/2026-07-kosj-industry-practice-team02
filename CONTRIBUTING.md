# CONTRIBUTING

## 작업 흐름

1. source-of-truth와 관련 ADR을 읽는다.
2. 작업 ID를 `TASKS.md`에서 확인하거나 새로 제안한다.
3. 복잡한 작업은 실행계획을 만든다.
4. 브랜치에서 구현한다.
5. 테스트·린트·타입체크·빌드·diff 리뷰를 수행한다.
6. 계약·문서·버전·데이터 계보를 갱신한다.
7. 구현 노트를 만들고 INDEX를 갱신한다.
8. 작은 논리 단위로 커밋한다.

## 브랜치 예시

```text
codex/DEV-001-repo-scaffold
codex/API-CHAT-001-chat-endpoint
codex/LOG-001-redaction-leak
codex/DOC-001-sync-decisions
```

새 독립 저장소의 기본 브랜치는 `main`이다. 구현 작업은 원칙적으로 `codex/<task-id>-<slug>` 브랜치에서 수행한다.

현재는 원격 저장소와 CI가 없다. 각 작업자는 local에서 lint·typecheck·test·build·contract parse/drift·secret scan을 실행하고 구현 노트에 명령과 결과를 남겨야 한다. 사용자가 Git 연결을 요청하기 전 원격·workflow·branch protection을 임의 생성하지 않는다.

## 커밋 예시

```text
feat(api): add typed chat fallback contract
feat(web): render server-provided source cards
test(security): verify raw question is never persisted
docs(impl): add IMP-20260713-001 discovery note
```

## 새 의존성

프로덕션 의존성 추가 전 다음을 기록하고 인간 승인을 받는다.

- 왜 표준 라이브러리/기존 의존성으로 해결할 수 없는가
- 라이선스·보안·유지관리 상태
- 번들/런타임/비용 영향
- 대안
- 제거/롤백 방법

개발 전용 의존성도 테스트/도구 가치와 유지비를 설명한다.

## PR/리뷰 체크

- 범위와 P0/P1/P2 일치
- 공개 API/DB 호환성
- 개인정보 원문 노출 여부
- ACTIVE KB 전용 검색
- mock/공식 데이터 표시
- 실패·빈 상태·장애 경로
- 접근성·모바일
- 테스트와 구현 노트
