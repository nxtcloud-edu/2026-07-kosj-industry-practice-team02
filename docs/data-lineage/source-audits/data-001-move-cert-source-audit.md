# DATA-001 전입·증명 출처 감사 요약

- 감사일: 2026-07-18
- 범위: `KB-MOVE-01..05`, `KB-CERT-01..05`
- 원 감사 SHA-256: `e009ee8dd14c1ef01f2ca4bffd32b363e72427160ab2e65b6e9d56f0759d6c4a`
- 경계: 공개 공식 페이지의 일반 안내만 요약한다. 개인 조회 결과·시민 질문 원문·인증 정보는 포함하지 않는다.

## 승인 근거 행렬

| ID | 공식 출처 / 제공기관 | URL | 사용 가능한 사실과 제한 |
|---|---|---|---|
| MOVE-01..03 | 전입신고 / 행정안전부 주민과 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01` | 인터넷·방문 경로, 본인·대리 경계, 근무시간 내 3시간, 수수료 없음. 특정 인증수단은 단정하지 않는다. |
| MOVE-04 | 주민등록 관련 통보서비스 / 행정안전부 주민과 | `https://plus.gov.kr/search/searchdtl/?srvcId=13110000039&typeSn=01` | 인터넷·방문 신청과 통보 범위만 사용한다. |
| MOVE-05 | 주민등록법 / 국가법령정보센터 | `https://www.law.go.kr/LSW/lsInfoP.do?lsId=001655&urlMode=lsInfoP` | 전입 후 14일 일반 원칙만 사용한다. 위반·과태료·개인 법률판단은 하지 않는다. |
| CERT-01..03 | 주민등록표 등본(초본) 발급 / 행정안전부 주민과 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01` | 등본·초본 의미, 인터넷·방문·무인 경로, 공식 수수료·처리 표시와 조건부 서류만 사용한다. |
| CERT-04 | 주민등록표 열람 / 행정안전부 주민과 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000014&typeSn=01` | 인터넷·방문, 즉시, 온라인 무료·방문 300원 범위만 사용한다. |
| CERT-05 | 무인민원발급안내 / 정부24(행정안전부) | `https://plus.gov.kr/portal/custcntr/utztngd/unmncvlcptissugd/` | 설치장소와 가능 민원 확인 경로만 사용한다. 전국 24시간·고정 수수료는 단정하지 않는다. |

## 재현 명령

```powershell
curl.exe -L -A "Mozilla/5.0" "<위 행렬의 URL>"
Get-FileHash -Algorithm SHA256 docs/data-lineage/source-audits/data-001-move-cert-source-audit.md
python -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1
```

이 요약은 PM 승인 증거가 아니다. PM은 승인 직전 URL과 변동 사실을 다시 확인한다.
