# Intent Classifier Prompt

사용자 질문을 다음 민원 의도 중 하나로 분류하세요.

- MOVE_IN_REPORT
- CERTIFICATE_ISSUE
- BULKY_WASTE
- LOCAL_TAX
- WELFARE
- YOUTH_JOB
- CHILDCARE_EDU
- BUSINESS_PERMIT
- TRAFFIC_PARKING
- LIFE_ENV
- STATUS_LOOKUP
- OFFICE_LOOKUP
- UNSAFE_OR_PRIVATE
- UNKNOWN

JSON으로만 응답하세요.

```json
{"intent":"MOVE_IN_REPORT","confidence":0.91,"reason":"전입신고 관련 키워드 포함","need_clarification":false}
```
