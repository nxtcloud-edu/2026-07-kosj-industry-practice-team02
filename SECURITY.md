# SECURITY.md

## 민감정보 보고

이 실습 저장소에는 실제 시민 개인정보, 실제 운영 비밀키, 실제 기관 내부자료를 올리지 않는다. 발견 시 즉시 커밋/배포를 중단하고 노출 범위를 확인한다. 비밀값은 회수·교체하고 Git 이력 정리가 필요한지 인간 책임자에게 보고한다.

## 금지 사항

- `.env`, API 키, Supabase service-role key 커밋
- 실제 주민등록번호·전화·상세주소·접수번호를 test fixture에 사용
- 질문 원문을 로그/DB/오류 추적에 기록
- LLM이 생성한 출처를 공식 근거로 표시
- 승인되지 않은 KB를 시민 답변에 노출
- mock 기관 정보를 실제처럼 표시

## 보안 관련 변경

마스킹, 로그, 권한, 보관기간, 외부 LLM, CORS, 배포 비밀, DB RLS/권한 변경은 반드시 인간 승인을 받고 ADR 또는 결정 로그를 남긴다.

자세한 정책은 `docs/07_SECURITY_PRIVACY.md`와 `docs/source-of-truth/PRIVACY_POLICY.md`를 따른다.
