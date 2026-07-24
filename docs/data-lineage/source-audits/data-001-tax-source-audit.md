# DATA-001 지방세 출처 감사 요약

- 감사일: 2026-07-18
- 범위: `KB-TAX-01..05`
- 원 감사 SHA-256: `4be9f4b371906ebdcadd5c96b9fe20b1d10b1d493e3e53f5bdd7081702e5de25`
- 경계: 공개 일반 경로와 민원 발급 범위만 요약한다. 개인 세액·체납·납부 결과는 저장하거나 단정하지 않는다.

## 승인 근거 행렬

| ID | 공식 출처 / 제공기관 | URL | 사용 가능한 사실과 제한 |
|---|---|---|---|
| TAX-01 | 위택스 / 행정안전부·한국지역정보개발원 | `https://www.wetax.go.kr/main.do` | 조회·납부 공식 경로와 전자납부번호 경로. 개인 결과는 안내하지 않는다. |
| TAX-02 | 위택스 로그인(자동차세 개인 고지 확인 경계) / 행정안전부·한국지역정보개발원 | `https://www.wetax.go.kr/login.do` | 본인 로그인 후 고지 확인 경로만 사용한다. 납기·세액·할인 혜택은 단정하지 않는다. |
| TAX-03 | 정부24 지방세 납세증명서 발급 / 행정안전부 지방세정책과 | `https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000056&tp_seq=01` | 인터넷·방문 신청, 즉시, 무료. 개인 체납 여부는 단정하지 않는다. |
| TAX-04 | 정부24 지방세 세목별 과세증명서 발급 / 행정안전부 지방세정책과 | `https://plus.gov.kr/search/searchdtl/?srvcId=13100000084&typeSn=05` | 인터넷 무료, 방문 수수료는 조례 기준. 개인 과세 결과는 안내하지 않는다. |
| TAX-05 | 정부24 지방세 납부확인서 발급 / 행정안전부 지방세정책과 | `https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13110000017&HighCtgCD=A09002&tp_seq=01` | 인터넷·방문, 즉시, 무료. 개인 납부 완료를 단정하지 않는다. |

TAX-03/05의 legacy 공식 URL은 임의의 deep-link로 교체하지 않는다. PM이 공식 UI에서 승인 직전 재확인한다.

## 재현 명령

```powershell
curl.exe -L -A "Mozilla/5.0" "<위 행렬의 URL>"
Get-FileHash -Algorithm SHA256 docs/data-lineage/source-audits/data-001-tax-source-audit.md
python -B scripts/validate_data_staging.py validate --draft-dir data/staging/data-001/0.1.0-draft.1
```

이 요약은 PM 승인 증거가 아니다.
