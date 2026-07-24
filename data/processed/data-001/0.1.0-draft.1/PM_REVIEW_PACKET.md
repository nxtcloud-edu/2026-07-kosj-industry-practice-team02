# DATA-001 PM 검수 완료 기록 — 0.1.0-draft.1

> **승인 검토 증거 / APPROVED_FOR_INITIAL_RELEASE**
> 이 문서는 hash-bound staging의 PM 전수 검토 기록입니다. 이는 official release·seed·ACTIVE 상태가 아니며, 해당 후속 작업은 DATA-SEED-001만 수행할 수 있습니다.

## 검수 범위와 제출 요약

- canonical content: KB 20, 기관 3, 기관×intent 매핑 12 (총 35행)
- PM reviewer: `PM-LOCAL-001`
- PM final confirmation/review time: `2026-07-19T02:06:19+09:00`
- final projection: KB 19 승인 / `KB-WASTE-03` 1건 보류 / 기관 3 승인 / 매핑 10 승인·2 반려
- PM은 검토 패키지의 AI 권고안을 전수 검토 후 최종 결정으로 확인했습니다. 새 source 조회나 새 사실 판단을 이 기록에 추가하지 않았습니다.
- 모든 source 확인일은 기존과 같이 `2026-07-18`입니다.

## KB 20건

| ID / label | source / verified | 안전한 범위 | AI 권고 | PM 최종 outcome |
|---|---|---|---|---|
| KB-CERT-01 / 등본과 초본의 차이 | [주민등록표 등본(초본) 발급](https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01) / 2026-07-18 | 등본은 세대, 초본은 한 사람의 주민등록 사항이라는 일반 구분; 제출처 요구는 단정하지 않음 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-CERT-02 / 주민등록등본 발급 방법 | [주민등록표 등본(초본) 발급](https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01) / 2026-07-18 | 인터넷·방문·무인 경로와 조건부 수수료·서류; 기기별 운영은 보장하지 않음 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-CERT-03 / 주민등록초본 발급 방법 | [주민등록표 등본(초본) 발급](https://plus.gov.kr/search/searchdtl/?srvcId=13100000015&typeSn=01) / 2026-07-18 | 신청 경로와 조건부 신청자격; 개인별 표시항목·외국인 적용은 단정하지 않음 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-CERT-04 / 주민등록표 열람 | [주민등록표 열람](https://plus.gov.kr/search/searchdtl/?srvcId=13100000014&typeSn=01) / 2026-07-18 | 열람과 발급 구분, 인터넷·방문 경로 및 공식 수수료 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-CERT-05 / 무인민원발급기 이용 안내 | [무인민원발급안내](https://plus.gov.kr/portal/custcntr/utztngd/unmncvlcptissugd/) / 2026-07-18 | 설치 장소와 발급 가능 민원 확인 경로; 24시간·고정 수수료로 일반화하지 않음 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-MOVE-01 / 전입신고 개요·신청방법 | [전입신고](https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01) / 2026-07-18 | 인터넷·방문, 본인·대리 경계, 즉시·무료 안내; 조건별 접수는 확인 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-MOVE-02 / 방문 전입신고 준비물 | [전입신고](https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01) / 2026-07-18 | 본인·대리·조건부 서류만; 신분증만으로 충분하다고 일반화하지 않음 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-MOVE-03 / 온라인 전입신고 | [전입신고](https://plus.gov.kr/search/searchdtl/?srvcId=13100000016&typeSn=01) / 2026-07-18 | 본인 온라인 신청과 방문 예외 경계; 특정 인증수단은 단정하지 않음 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-MOVE-04 / 주민등록 관련 통보서비스 | [주민등록 관련 통보서비스](https://plus.gov.kr/search/searchdtl/?srvcId=13110000039&typeSn=01) / 2026-07-18 | 전입신고와 별개의 통보 범위 및 신청 경로 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-MOVE-05 / 주민등록법상 신고 일반 원칙·주의사항 | [주민등록법](https://www.law.go.kr/LSW/lsInfoP.do?lsId=001655&urlMode=lsInfoP) / 2026-07-18 | 전입 후 14일 일반 원칙만; 위반·과태료·개인 법률 판단은 제외 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-TAX-01 / 지방세 온라인 납부 공식 경로 안내 | [위택스](https://www.wetax.go.kr/main.do) / 2026-07-18 | 위택스·전자납부번호 경로; 개인 세액·체납·완료 결과는 제외 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-TAX-02 / 자동차세 개인 고지 확인·납부의 공식 로그인 경로 | [위택스 로그인](https://www.wetax.go.kr/login.do) / 2026-07-18 | **본인 로그인 후 개인 고지 확인 경로만**; 납기·세액·혜택·체납은 제외 | APPROVE_INITIAL_RELEASE; PM KEEP | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-TAX-03 / 지방세 납세증명서 발급 안내 | [정부24 지방세 납세증명서 발급](https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13100000056&tp_seq=01) / 2026-07-18 | 신청 경로·즉시·무료; 개인 체납 판단은 제외 | APPROVE_INITIAL_RELEASE; **PM KEEP: exact plus.gov deep-link 및 최신 표시 재확인** | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-TAX-04 / 지방세 세목별 과세증명서 발급 안내 | [정부24 지방세 세목별 과세증명서 발급](https://plus.gov.kr/search/searchdtl/?srvcId=13100000084&typeSn=05) / 2026-07-18 | 증명 경로와 인터넷 무료/방문 조례 경계; 개인 결과는 제외 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-TAX-05 / 지방세 납부확인서 발급 안내 | [정부24 지방세 납부확인서 발급](https://www.gov.kr/mw/AA020InfoCappView.do?CappBizCD=13110000017&HighCtgCD=A09002&tp_seq=01) / 2026-07-18 | 인터넷·방문·즉시·무료; 납부 완료 결과는 제외 | APPROVE_INITIAL_RELEASE; **PM KEEP: exact plus.gov deep-link 및 최신 표시 재확인** | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-WASTE-01 / 대형폐기물 배출신청 절차 | [배출신청안내](https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null) / 2026-07-18 | 홈페이지·지정판매소 절차와 결제 완료 조건; 수거 시점은 보장하지 않음 | APPROVE_INITIAL_RELEASE; PM KEEP: 운영 재확인 | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-WASTE-02 / 대형폐기물 결제·스티커·변경·환불 안내 | [배출신청안내](https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null) / 2026-07-18 | 결제·출력·취소/환불 조건; 안내 기간은 SLA가 아님 | APPROVE_INITIAL_RELEASE; PM KEEP: 환불 조건 재확인 | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| **KB-WASTE-03 / 침대 프레임 배출 수수료** | [배출항목선택](https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305) / 2026-07-18 | 1인용침대 8,000원·2인용침대 10,000원; 매트리스·임의 규격 분류 제외 | **WITHHOLD_FOR_REGRESSION** | 완료 — WITHHOLD_FOR_REGRESSION; REG-001 전 initial release 제외 확인 |
| KB-WASTE-04 / 매트리스 배출 수수료 | [배출항목선택](https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305) / 2026-07-18 | 공식 매트 품목·금액만; 프레임·비열거 품목은 제외 | APPROVE_INITIAL_RELEASE; PM KEEP: 수수료 재확인 | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| KB-WASTE-05 / 대형폐기물 배출요일·수거 문의 | [배출신청안내](https://www.sjwaste.kr/board?menuId=MENU00303&siteId=null) / 2026-07-18 | 지역 분류별 일정 확인 경로; 동별·당일 수거를 보장하지 않음 | APPROVE_INITIAL_RELEASE; PM KEEP: 요일 재확인 | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |

## 공식 기관 3건

| ID / label | source / verified | 안전한 범위 | AI 권고 | PM 최종 outcome |
|---|---|---|---|---|
| OFFICE-AREUM / 아름동 행정복지센터 | [세종시 찾아오시는 길](https://www.sejong.go.kr/areum/sub02_02.do?cmsNo=1461) / 2026-07-18 | 공식명·주소·대표전화·업무시간; Kakao는 위치 링크일 뿐 provenance 아님 | APPROVE_INITIAL_RELEASE; PM KEEP: 최신 재확인 | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-DODAM / 도담동 행정복지센터 | [세종시 찾아오시는 길](https://www.sejong.go.kr/dodam/sub02_02.do?cmsNo=1458) / 2026-07-18 | 공식명·주소·대표전화·업무시간; Kakao는 위치 링크일 뿐 provenance 아님 | APPROVE_INITIAL_RELEASE; PM KEEP: 최신 재확인 | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-JOCHIWON / 북세종 통합 행정복지센터 | [세종시 찾아오시는 길](https://www.sejong.go.kr/jochiwon/sub02_02.do?cmsNo=1425) / 2026-07-18 | 공식명·주소·대표전화·업무시간; Kakao는 위치 링크일 뿐 provenance 아님 | APPROVE_INITIAL_RELEASE; PM KEEP: 최신 재확인 | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |

## 기관×intent 매핑 12건

| ID / label | source / verified | 안전한 범위 | AI 권고 | PM 최종 outcome |
|---|---|---|---|---|
| OFFICE-AREUM:BULKY_WASTE / 안전도시과 환경경제 | [아름동 업무안내](https://www.sejong.go.kr/areum/sub02_01.do?cmsNo=1460) / 2026-07-18 | 생활폐기물·청소 관련 1차 문의 힌트; 신청·요금 근거 아님 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-AREUM:CERTIFICATE_ISSUANCE / 민원행정과 일반민원 | [아름동 업무안내](https://www.sejong.go.kr/areum/sub02_01.do?cmsNo=1460) / 2026-07-18 | 통합민원·주민등록 관련 1차 문의 힌트; 모든 증명서 처리 보장 아님 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| **OFFICE-AREUM:LOCAL_TAX_GENERAL / 민원행정과 세무부동산** | [아름동 업무안내](https://www.sejong.go.kr/areum/sub02_01.do?cmsNo=1460) / 2026-07-18 | 취득세·등록면허세 근거만 확인; 지방세 일반 전체로 확대하지 않음 | **REJECT** | 완료 — REJECT; 직접 책임 근거 부족으로 initial release 제외 확인 |
| OFFICE-AREUM:MOVE_IN_RESIDENT_REGISTRATION / 민원행정과 일반민원 | [아름동 업무안내](https://www.sejong.go.kr/areum/sub02_01.do?cmsNo=1460) / 2026-07-18 | 주민등록·통합민원 1차 문의 힌트 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| **OFFICE-DODAM:BULKY_WASTE / 주민생활** | [도담동 업무안내](https://www.sejong.go.kr/dodam/sub02_01.do?cmsNo=1457) / 2026-07-18 | 환경 표기만 있고 대형폐기물 직접 담당 근거 없음 | **REJECT** | 완료 — REJECT; 직접 책임 근거 부족으로 initial release 제외 확인 |
| OFFICE-DODAM:CERTIFICATE_ISSUANCE / 민원행정 | [도담동 업무안내](https://www.sejong.go.kr/dodam/sub02_01.do?cmsNo=1457) / 2026-07-18 | 통합민원·인감·무인발급기 1차 문의 힌트; 증명서별 보장 아님 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-DODAM:LOCAL_TAX_GENERAL / 민원행정 | [도담동 업무안내](https://www.sejong.go.kr/dodam/sub02_01.do?cmsNo=1457) / 2026-07-18 | 지방세 업무 표기에 근거한 1차 문의 힌트 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-DODAM:MOVE_IN_RESIDENT_REGISTRATION / 민원행정 | [도담동 업무안내](https://www.sejong.go.kr/dodam/sub02_01.do?cmsNo=1457) / 2026-07-18 | 주민등록·통합민원 1차 문의 힌트 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-JOCHIWON:BULKY_WASTE / 안전도시과 청소환경 | [조치원읍 업무안내](https://www.sejong.go.kr/jochiwon/sub02_01.do?cmsNo=1424) / 2026-07-18 | 폐기물·생활폐기물 수거 관리 1차 문의 힌트 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-JOCHIWON:CERTIFICATE_ISSUANCE / 민원행정과 일반민원 | [조치원읍 업무안내](https://www.sejong.go.kr/jochiwon/sub02_01.do?cmsNo=1424) / 2026-07-18 | 등초본·인감 관련 1차 문의 힌트 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-JOCHIWON:LOCAL_TAX_GENERAL / 민원행정과 세무부동산 | [조치원읍 업무안내](https://www.sejong.go.kr/jochiwon/sub02_01.do?cmsNo=1424) / 2026-07-18 | 지방세(조치원권역) 1차 문의 힌트 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |
| OFFICE-JOCHIWON:MOVE_IN_RESIDENT_REGISTRATION / 민원행정과 일반민원 | [조치원읍 업무안내](https://www.sejong.go.kr/jochiwon/sub02_01.do?cmsNo=1424) / 2026-07-18 | 전입·재등록·전입세대 확인 관련 1차 문의 힌트 | APPROVE_INITIAL_RELEASE | 완료 — APPROVE_INITIAL_RELEASE; 제출 출처·안전 범위·표현·초기 릴리스 포함 확인 |

## 완료된 PM 확인과 다음 경계

1. PM은 35행 각각의 submitted source, safe scope, expression 및 disposition을 검토 패킷 기준으로 확인했고, manifest의 record별 decision/comment에 기록했습니다.
2. `KB-WASTE-03`은 REG-001 전까지 initial release에 포함하지 않습니다.
3. `OFFICE-AREUM:LOCAL_TAX_GENERAL`, `OFFICE-DODAM:BULKY_WASTE`는 직접 책임 근거가 충분하지 않아 initial release에 포함하지 않습니다.
4. 작성자 `AI-DATA-BACKEND`와 PM reviewer `PM-LOCAL-001`은 다릅니다.
5. 후속 DATA-SEED-001은 이 승인 증거를 입력으로 검토할 수 있으나, immutable official release·DB seed/import·ACTIVE 전환은 이 문서나 DATA-001이 수행하지 않습니다.
