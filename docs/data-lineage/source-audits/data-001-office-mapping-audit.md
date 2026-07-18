# DATA-001 기관·민원 매핑 출처 감사 요약

- 감사일: 2026-07-18
- 범위: 기관 3건, 기관×민원 매핑 12건
- 원 감사 SHA-256: `2f8c2e3f3d21650ccc7fb58192dfa4092cc5f5115b58eccef2ba4c3f012732a6`
- 경계: 기관 공개 연락처·업무시간과 공식 담당업무 페이지만 사용한다. Kakao URL은 위치 링크이며 provenance가 아니다.

## 기관 사실 행렬

| ID | 기관 / 지역 | 주소 / 전화 / 운영시간 | 공식 사실 URL / 지도 URL |
|---|---|---|---|
| OFFICE-AREUM | 아름동 행정복지센터 / 아름동 | `(30100) 세종특별자치시 보듬3로 114(아름동)` / `044-301-6300` / 평일 09:00~18:00 | `https://www.sejong.go.kr/areum/sub02_02.do?cmsNo=1461` / `https://place.map.kakao.com/26471721` |
| OFFICE-DODAM | 도담동 행정복지센터 / 도담동 | `(30098) 세종특별자치시 보람로 77(도담동)` / `044-301-6200` / 평일 09:00~18:00 | `https://www.sejong.go.kr/dodam/sub02_02.do?cmsNo=1458` / `https://place.map.kakao.com/23346315` |
| OFFICE-JOCHIWON | 북세종 통합 행정복지센터 / 조치원읍 | `(30024) 세종특별자치시 조치원읍 새내16길 17` / `044-301-5000` / 평일 09:00~18:00 | `https://www.sejong.go.kr/jochiwon/sub02_02.do?cmsNo=1425` / `https://place.map.kakao.com/19342218` |

## 담당업무 행렬

| 기관 | 근거 URL | BULKY_WASTE | CERTIFICATE_ISSUANCE | LOCAL_TAX_GENERAL | MOVE_IN_RESIDENT_REGISTRATION |
|---|---|---|---|---|---|
| OFFICE-AREUM | `https://www.sejong.go.kr/areum/sub02_01.do?cmsNo=1460` | 안전도시과 환경경제 / APPROVE | 민원행정과 일반민원 / APPROVE | 민원행정과 세무부동산 / REJECT | 민원행정과 일반민원 / APPROVE |
| OFFICE-DODAM | `https://www.sejong.go.kr/dodam/sub02_01.do?cmsNo=1457` | 주민생활 / REJECT | 민원행정 / APPROVE | 민원행정 / APPROVE | 민원행정 / APPROVE |
| OFFICE-JOCHIWON | `https://www.sejong.go.kr/jochiwon/sub02_01.do?cmsNo=1424` | 안전도시과 청소환경 / APPROVE | 민원행정과 일반민원 / APPROVE | 민원행정과 세무부동산 / APPROVE | 민원행정과 일반민원 / APPROVE |

## 재현 명령

```powershell
curl.exe -L -A "Mozilla/5.0" "<위 행렬의 공식 사실 또는 담당업무 URL>"
Get-FileHash -Algorithm SHA256 docs/data-lineage/source-audits/data-001-office-mapping-audit.md
python -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1
```

두 REJECT 권고는 근거 보강 전 승인하지 않는다. 이 요약은 PM 승인 증거가 아니다.
