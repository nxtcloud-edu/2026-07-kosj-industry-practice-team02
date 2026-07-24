# DATA-001 대형폐기물 출처 감사 요약

- 감사일: 2026-07-18
- 범위: `KB-WASTE-01..05`
- 원 감사 SHA-256: `c3da78be3a3f94848850db4694fe39c7d2889c58830f17ebb34850c1e59d0e34`
- 제공기관: 세종특별자치시시설관리공단
- 경계: 공개 일반 절차·품목 요금만 요약하며 개인 신청·결제·접수 결과는 포함하지 않는다.

## 승인 근거 행렬

| ID | 공식 출처 | URL | 사용 가능한 사실과 제한 |
|---|---|---|---|
| WASTE-01,02,05 | 배출신청안내 | `https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null` | 신청·결제·취소/환불 조건·요일·문의 경로. 일정 처리 SLA는 단정하지 않는다. |
| WASTE-03,04 | 배출항목선택 | `https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305` | 침대 프레임 8,000/10,000원, 매트 4,000/6,000/4,000원. 프레임과 매트를 혼동하지 않는다. |

`KB-WASTE-03`은 회귀 표본 보존을 위해 `WITHHOLD_FOR_REGRESSION` 권고이며 ACTIVE·initial release 대상이 아니다.

## 재현 명령

```powershell
curl.exe -L -A "Mozilla/5.0" "https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null"
curl.exe -L -A "Mozilla/5.0" "https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305"
Get-FileHash -Algorithm SHA256 docs/data-lineage/source-audits/data-001-waste-source-audit.md
python -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1
```

이 요약은 PM 승인 증거가 아니다. 운영 조건과 요금은 승인 직전 다시 확인한다.
