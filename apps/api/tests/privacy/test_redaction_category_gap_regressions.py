from __future__ import annotations

import pytest

from sejong_ai_api.privacy import PiiCategory, redact_question


@pytest.mark.parametrize(
    ("raw", "expected_category", "expected_masked_text"),
    [
        ("제 성함은 독고준입니다.", PiiCategory.NAME, "제 성함은 [이름]입니다."),
        ("성함: 독고준", PiiCategory.NAME, "성함: [이름]"),
        ("독고준입니다.", PiiCategory.NAME, "[이름]입니다."),
        (
            "M12345678인데 재발급해야 하나요?",
            PiiCategory.PASSPORT_OR_LICENSE,
            "[여권·면허번호]인데 재발급해야 하나요?",
        ),
        (
            "11-12-123456-78인데 갱신해야 하나요?",
            PiiCategory.PASSPORT_OR_LICENSE,
            "[여권·면허번호]인데 갱신해야 하나요?",
        ),
        (
            "세종 12-34-567890-12로 조회해 주세요.",
            PiiCategory.PASSPORT_OR_LICENSE,
            "[여권·면허번호]로 조회해 주세요.",
        ),
        (
            "123-456789-12-345로 환급받고 싶어요.",
            PiiCategory.FINANCIAL_ACCOUNT,
            "[계좌번호]로 환급받고 싶어요.",
        ),
        (
            "환급받을 곳은 123-456789-12-345입니다.",
            PiiCategory.FINANCIAL_ACCOUNT,
            "환급받을 곳은 [계좌번호]입니다.",
        ),
        (
            "4000 0000 0000 0000 006로 결제했어요.",
            PiiCategory.PAYMENT_CARD,
            "[카드번호]로 결제했어요.",
        ),
        (
            "본인인증용 확인번호는 654321입니다.",
            PiiCategory.AUTH_SECRET,
            "본인인증용 확인번호는 [인증정보]입니다.",
        ),
        (
            "문자로 받은 6자리 코드는 654321이에요.",
            PiiCategory.AUTH_SECRET,
            "문자로 받은 6자리 코드는 [인증정보]이에요.",
        ),
        (
            "인증키 ABCD-1234를 입력했어요.",
            PiiCategory.AUTH_SECRET,
            "인증키 [인증정보]를 입력했어요.",
        ),
        (
            "보안키는 QWER-1234입니다.",
            PiiCategory.AUTH_SECRET,
            "보안키는 [인증정보]입니다.",
        ),
        (
            "서울 중구 가 1234로 등록돼 있어요.",
            PiiCategory.VEHICLE_PLATE,
            "[차량번호]로 등록돼 있어요.",
        ),
        (
            "외교 001-001 번호판입니다.",
            PiiCategory.VEHICLE_PLATE,
            "[차량번호] 번호판입니다.",
        ),
        (
            "대형폐기물 신청번호 SJ-2026-123456이에요.",
            PiiCategory.CASE_REFERENCE,
            "대형폐기물 신청번호 [접수번호]이에요.",
        ),
        (
            "전입신고 처리번호 SJ-2026-123456입니다.",
            PiiCategory.CASE_REFERENCE,
            "전입신고 처리번호 [접수번호]입니다.",
        ),
        (
            "배출번호는 2026-07-123456입니다.",
            PiiCategory.CASE_REFERENCE,
            "배출번호는 [접수번호]입니다.",
        ),
        (
            "세종시 금남면 도남리 123-4로 이사했어요.",
            PiiCategory.DETAILED_ADDRESS,
            "[상세주소]로 이사했어요.",
        ),
        (
            "세종시 연기면 보통리 123에 살아요.",
            PiiCategory.DETAILED_ADDRESS,
            "[상세주소]에 살아요.",
        ),
        (
            "금남면 도남리 산 12-3입니다.",
            PiiCategory.DETAILED_ADDRESS,
            "[상세주소]입니다.",
        ),
        (
            "저는 파킨슨병이 있어요.",
            PiiCategory.SENSITIVE_HEALTH_WELFARE,
            "저는 [건강·복지정보]이 있어요.",
        ),
        (
            "저는 루푸스가 있어요.",
            PiiCategory.SENSITIVE_HEALTH_WELFARE,
            "저는 [건강·복지정보]가 있어요.",
        ),
        (
            "임신했어요.",
            PiiCategory.SENSITIVE_HEALTH_WELFARE,
            "[건강·복지정보]했어요.",
        ),
        (
            "투석 중입니다.",
            PiiCategory.SENSITIVE_HEALTH_WELFARE,
            "[건강·복지정보]입니다.",
        ),
        (
            "저는 의료급여 대상자입니다.",
            PiiCategory.SENSITIVE_HEALTH_WELFARE,
            "저는 [건강·복지정보]입니다.",
        ),
        (
            "생계급여 수급자예요.",
            PiiCategory.SENSITIVE_HEALTH_WELFARE,
            "[건강·복지정보]예요.",
        ),
        (
            "경도 127.289, 위도 36.480입니다.",
            PiiCategory.PRECISE_LOCATION,
            "경도 [정밀위치]입니다.",
        ),
        (
            "북위 36도 30분, 동경 127도 15분입니다.",
            PiiCategory.PRECISE_LOCATION,
            "북위 [정밀위치]입니다.",
        ),
    ],
)
def test_category_gap_is_masked_exactly(
    raw: str,
    expected_category: PiiCategory,
    expected_masked_text: str,
) -> None:
    result = redact_question(raw)

    assert result.masked_text == expected_masked_text
    assert [finding.category for finding in result.findings] == [expected_category]
    assert result.safe_for_failure_storage is True
    assert result.safe_for_synthetic_provider is True
    assert result.unresolved_reason is None


@pytest.mark.parametrize(
    ("raw", "raw_sentinel"),
    [
        ("전입신고 김철수 후 주소 변경은 언제 하나요?", "김철수"),
        ("SJ-2026-123456 전입신고 후 주소 변경은 언제 하나요?", "SJ-2026-123456"),
        ("123-456-789012 전입신고 후 주소 변경은 언제 하나요?", "123-456-789012"),
        ("11-12-123456-78 전입신고 후 주소 변경은 언제 하나요?", "11-12-123456-78"),
    ],
)
def test_question_grammar_with_raw_sentinel_never_fails_open(
    raw: str,
    raw_sentinel: str,
) -> None:
    result = redact_question(raw)

    if result.masked_text is None:
        assert result.safe_for_failure_storage is False
        assert result.safe_for_synthetic_provider is False
        assert result.unresolved_reason is not None
    else:
        assert raw_sentinel not in result.masked_text
        assert result.masked_text != raw
        assert result.findings


def _assert_never_unchanged_safe(raw: str, forbidden_values: tuple[str, ...]) -> None:
    result = redact_question(raw)

    assert not (
        result.masked_text == raw
        and not result.findings
        and result.safe_for_failure_storage is True
        and result.safe_for_synthetic_provider is True
        and result.unresolved_reason is None
    )
    if result.masked_text is None:
        assert result.safe_for_failure_storage is False
        assert result.safe_for_synthetic_provider is False
        assert result.unresolved_reason is not None
    else:
        assert result.masked_text != raw
        assert result.findings
        assert all(value not in result.masked_text for value in forbidden_values)


@pytest.mark.parametrize(
    ("raw", "synthetic_name"),
    [
        ("전입신고 남궁민 후 문의", "남궁민"),
        ("주민등록 독고준 관련 문의", "독고준"),
        ("대형폐기물 황보라 신청 처리", "황보라"),
    ],
)
def test_contextual_name_insertion_never_fails_open(
    raw: str,
    synthetic_name: str,
) -> None:
    _assert_never_unchanged_safe(raw, (synthetic_name,))


@pytest.mark.parametrize(
    "raw",
    [
        "김철수 주소는 어디까지 써야 하나요?",
        "새 김철수 주소가 등본에 아직 안 나와요.",
        "증명서 김철수 전화번호를 잘못 입력했어요.",
        "김철수 새 주소가 등본에 아직 안 나와요.",
        "김철수 주민번호를 가린 등본도 발급되나요?",
        "김철수 차량 번호가 없어도 자동차세를 낼 수 있나요?",
        "김철수 등본 주소가 잘못 나왔어요.",
        "김철수 환급 계좌는 납세자 이름과 같아야 하나요?",
        "지방세 김철수 고지서 주민번호가 그대로 보여요.",
    ],
)
def test_name_before_pii_label_never_fails_open(raw: str) -> None:
    _assert_never_unchanged_safe(raw, ("김철수",))


@pytest.mark.parametrize(
    ("raw", "forbidden_values"),
    [
        (
            "전입신고 ９００１０１－１２３４５６７ 문의",
            ("９００１０１－１２３４５６７", "900101-1234567"),
        ),
        (
            "전입신고 김\u200b철수 후 문의",
            ("김\u200b철수", "김철수"),
        ),
        (
            "계좌번호 123-456\u0338789-12-345 환급 문의",
            ("123-456\u0338789-12-345", "123-456789-12-345"),
        ),
        (
            "차량번호 12가34\u20e356 문의",
            ("12가34\u20e356", "12가3456"),
        ),
    ],
    ids=("nfkc-fullwidth", "zero-width-removal", "combining-mark", "keycap"),
)
def test_unicode_identifier_bypass_never_fails_open(
    raw: str,
    forbidden_values: tuple[str, ...],
) -> None:
    _assert_never_unchanged_safe(raw, forbidden_values)


@pytest.mark.parametrize(
    ("raw", "normalized_sentinel"),
    [
        ("11-1\u20e32-123456-78", "11-12-123456-78"),
        ("123-456\u20e3789-12-345", "123-456789-12-345"),
        ("SJ-2026-123\u20e3456", "SJ-2026-123456"),
        ("S\u0301J-2026-123456", "ŚJ-2026-123456"),
    ],
)
def test_unlabeled_unicode_identifier_bypass_never_fails_open(
    raw: str,
    normalized_sentinel: str,
) -> None:
    _assert_never_unchanged_safe(raw, (raw, normalized_sentinel))


@pytest.mark.parametrize(
    "identifier_parts",
    [
        ("11", "12", "123456", "78"),
        ("123", "456789", "12", "345"),
        ("SJ", "2026", "123456"),
        ("12", "가", "3456"),
    ],
    ids=("license", "account", "case", "vehicle"),
)
@pytest.mark.parametrize(
    "separator",
    [" ", "/", ":", "\u2013"],
    ids=("space", "slash", "colon", "en-dash"),
)
def test_identifier_separator_matrix_never_fails_open(
    identifier_parts: tuple[str, ...],
    separator: str,
) -> None:
    identifier = separator.join(identifier_parts)
    raw = f"{identifier} 처리 문의"

    _assert_never_unchanged_safe(raw, (identifier,))


@pytest.mark.parametrize(
    "raw",
    [
        "본명은 알렉산더입니다.",
        "제 본명은 브라이언이에요.",
        "M 12345678로 재발급 문의합니다.",
        "환급받을 곳은 123456-78-901234입니다.",
        "123-456789-12345로 보내 주세요.",
        "3530 0000 0000 0003로 결제했어요.",
        "6200 0000 0000 0000 000로 결제했어요.",
        "로그인 암호는 Qwer-1234입니다.",
        "문자인증값은 654321입니다.",
        "일회용 번호는 654321입니다.",
        "배출신고번호는 2026-07-123456입니다.",
        "세종 아름동 가-1234로 등록돼 있어요.",
        "외교 001 001 번호판입니다.",
        "도담동 가온빌 302호에 살아요.",
        "어진동 세종타워 7층입니다.",
        "새롬동 행복주택 A동 1203호입니다.",
        "저는 신장병이 있어요.",
        "저는 크론병이 있어요.",
        "저는 시각장애가 있어요.",
        "현재 임신 12주예요.",
        "저는 주거급여 수급자예요.",
        "의료급여 수급자입니다.",
        "북위 36.480, 동경 127.289입니다.",
        "동경 127도 15분, 북위 36도 30분입니다.",
        "북위 36도 30분 10초, 동경 127도 15분 20초입니다.",
        "실명은 아나스타샤입니다.",
        "제 실명은 라훌쿠마르예요.",
        "AB 1234567이 여권 번호예요.",
        "1000-1234-5678로 보내 주세요.",
        "123-45-678901로 입금해 주세요.",
        "6200 0000 0000 0005로 결제했어요.",
        "6200 0000 0000 0000 05로 결제했어요.",
        "5600 0000 0000 0003로 결제했어요.",
        "접속 암호는 Abcd-1234입니다.",
        "문자 확인 코드는 765432입니다.",
        "본인인증 값은 456789입니다.",
        "준외 001-001 번호판입니다.",
        "도담동 가온빌딩 302호에 살아요.",
        "어진동 세종센터 7층입니다.",
        "새롬동 리버뷰 B동 1203호입니다.",
        "저는 뇌전증이 있어요.",
        "저는 조현병이 있어요.",
        "저는 청각장애가 있어요.",
        "저는 교육급여 수급자예요.",
        "한부모가정입니다.",
        "동경 127.289, 북위 36.480입니다.",
        "북위 36.480도, 동경 127.289도입니다.",
        "위도 36.480 / 경도 127.289입니다.",
        "N 36.480, E 127.289 좌표예요.",
        "김철수의 전입신고 방법을 알려주세요.",
        "지방세 고지서가 김철수에게 왔어요.",
        "등록명은 아나스타샤입니다.",
        "제 호적명은 라훌쿠마르예요.",
        "123456789로 영국 여권 갱신 문의합니다.",
        "C01X00T47이 제 여권 번호예요.",
        "환급받을 곳은 1234-01-123456입니다.",
        "020-123456-123으로 보내 주세요.",
        "6200 0000 0000 0000 0로 결제했어요.",
        "5600 0000 0000 0000 03로 결제했어요.",
        "일회용 암호는 Abcd-1234입니다.",
        "접속 비밀키는 Secret-5678입니다.",
        "본인확인 숫자는 654321입니다.",
        "문자 확인값은 765432입니다.",
        "영사 001-001 번호판입니다.",
        "국기 001-001 번호판입니다.",
        "도담동 가온하우스 B102호에 살아요.",
        "어진동 세종센터 지하 1층입니다.",
        "저는 심부전이 있어요.",
        "저는 간경화가 있어요.",
        "저는 지체장애가 있어요.",
        "저는 기초연금 수급자예요.",
        "독거노인 지원대상자입니다.",
        "36°28'48\"N, 127°17'20\"E 좌표예요.",
        "도담동 가온하우스 지하 B1호에 살아요.",
        "8100 0000 0000 0002로 결제했어요.",
        "보안 토큰은 ZXCV-9876입니다.",
        "협정 001-001 번호판입니다.",
    ],
)
def test_adjacent_actual_pii_never_fails_open(raw: str) -> None:
    _assert_never_unchanged_safe(raw, (raw,))


@pytest.mark.parametrize(
    "raw",
    [
        "전입신고서를 쓸 때 새 주소는 어느 항목에 적나요?",
        "전입신고에 상세주소를 반드시 적어야 하나요?",
        "새 주소가 확정되지 않았는데 전입신고가 가능한가요?",
        "전입신고 신청서에 주민등록번호 전체를 써야 하나요?",
        "휴대폰이 없으면 전입신고 연락처를 어떻게 적나요?",
        "전입신고 본인확인 코드를 다시 요청할 수 있나요?",
        "현재 위치를 공유하지 않고 전입신고할 수 있나요?",
        "등본 주소가 최신 정보인지 어디서 확인하나요?",
        "증명서 신청서에 이름을 어떻게 적어야 하나요?",
        "주민번호 비공개 증명서는 어떻게 발급하나요?",
        "증명서 발급 때 전화 연락처가 필수인가요?",
        "초본을 받을 메일 주소는 나중에 바꿀 수 있나요?",
        "카드 번호를 보관하지 않고 결제할 수 있나요?",
        "배출 주소를 모를 때는 어떻게 신고하나요?",
        "대형폐기물 배출 위치 선택을 취소할 수 있나요?",
        "신고서에 신청자 이름이 꼭 들어가야 하나요?",
        "수거 연락용 전화번호를 나중에 고칠 수 있나요?",
        "대형폐기물 알림용 이메일을 바꿀 수 있나요?",
        "신고 처리번호를 잃어버리면 어떻게 하나요?",
        "대형폐기물 보안 코드를 다시 발급받을 수 있나요?",
        "고지서에 납세자 이름이 틀리면 어디에 알리나요?",
        "지방세 확인서에 성명을 한글로만 표시하나요?",
        "전자고지 이메일을 새로 등록하는 방법이 궁금해요.",
        "지방세 신청번호는 납부 후에도 확인할 수 있나요?",
        "지방세 로그인 비밀번호를 다시 만들 수 있나요?",
        "자동차세를 카드 번호 입력 없이 낼 수 있나요?",
        "지방세 환급용 계좌를 등록하지 않아도 되나요?",
        "담당 읍면동은 현재 주소를 기준으로 고르나요?",
        "전입신고서에서 신청인 성명을 고치는 방법이 있나요?",
        "전입신고 결과에 이름이 다르게 나오면 어떻게 하나요?",
        "발급된 증명서의 성명 오자를 정정할 수 있나요?",
        "면 이름을 선택하면 공식 기관 카드가 표시되나요?",
        "온라인 전입신고 비번을 초기화할 수 있나요?",
        "온라인 증명서 패스워드 초기화 절차가 궁금해요.",
        "신고 비밀번호 초기화 후에도 신청 내역이 남나요?",
        "납부 인증 문자가 늦게 오면 다시 요청할 수 있나요?",
        "전입신고할 때 거주지는 어디까지 써야 합니까?",
        "이사 후 주소 정정은 온라인으로도 됩니까?",
        "새 주소 입력란이 비어 있으면 접수할 수 없나요?",
        "상세주소 없이도 전입 처리가 되는지 알고 싶습니다.",
        "전입신고 화면에서 이름 표시를 바꿀 수 있을까요?",
        "주민등록번호 공개 여부는 어디서 선택합니까?",
        "전입신고 연락처 입력란은 비워 두어도 되나요?",
        "전입신고 이메일 변경 절차를 알고 싶습니다.",
        "접수 번호를 분실한 경우 다시 확인하는 방법은 무엇입니까?",
        "GPS 정보를 제공하지 않아도 전입신고가 됩니까?",
        "등본에 표시된 거주지를 고치려면 어디로 문의합니까?",
        "등본의 주민등록번호를 전부 가릴 수 있을까요?",
        "주민 번호 앞자리만 보이게 신청하려면 어디서 선택하죠?",
        "증명서 신청에 연락처 제공이 꼭 필요합니까?",
        "카드번호 저장 여부를 사용자가 선택할 수 있습니까?",
        "대형폐기물 배출지 주소를 신고 후에도 정정할 수 있습니까?",
        "위치 정보 제공에 동의하지 않아도 신고 가능합니까?",
        "수거 연락처 변경은 접수 후에도 가능합니까?",
        "신고 알림을 받을 메일을 변경하고 싶습니다.",
        "배출 신고 번호는 접수 직후 생성됩니까?",
        "결제 카드 번호를 다시 입력해야 합니까?",
        "지방세 고지서를 받을 주소는 온라인에서 바꿀 수 있습니까?",
        "고지 주소 변경이 다음 달부터 적용되는지 궁금합니다.",
        "고지서 주민등록번호 숨김을 신청할 수 있을까요?",
        "지방세 연락처를 제공하지 않아도 전자고지를 받을 수 있습니까?",
        "전자고지 메일 주소를 바꾸는 메뉴가 어디에 있습니까?",
        "지방세 접수 코드는 납부 완료 후에도 유효합니까?",
        "계좌번호 변경 신청에 본인 인증이 필요합니까?",
        "담당 동은 이사 전 주소와 새 주소 중 무엇으로 고릅니까?",
        "주민번호 뒷자리 숨김 설정은 나중에 변경되나요?",
        "결과 알림 메일을 받지 않도록 설정할 수 있을까요?",
        "메일 대신 문자 알림을 선택할 수 있을까요?",
        "카드 정보를 입력하지 않고 수수료를 낼 수 있을까요?",
        "수거 장소와 거주지가 달라도 신청할 수 있을까요?",
        "대형폐기물 신청자 성함이 틀렸을 때 고칠 수 있나요?",
        "전화 번호 변경이 납부 내역에도 반영되나요?",
        "이메일 고지를 해지하면 종이 고지서가 오나요?",
        "차량 번호 변경 사실을 세무 부서에 알려야 합니까?",
        "번호판 교체 후 자동차세 정보는 언제 갱신되나요?",
        "면 명칭이 바뀐 경우 어떤 항목을 골라야 합니까?",
        "주민센터 기관 카드는 선택한 동 기준으로 나오나요?",
        "읍·면·동을 다시 고르면 담당 기관도 바뀝니까?",
        "전입할 읍면동을 선택 목록에서 찾을 수 없습니다.",
        "전입신고서 신청인 이름을 정정하고 싶어요.",
        "발급 신청서의 신청인 성함을 수정하고 싶습니다.",
        "증명서 이름 표기가 다르면 재발급해야 합니까?",
        "성명 변경 후 등본에는 언제 반영되는지 궁금합니다.",
        "납세자 이름 오기는 어떤 창구에서 정정하나요?",
        "지방세 문서의 성명 표기를 수정하고 싶습니다.",
        "동 이름 검색이 안 될 때 직접 선택할 수 있을까요?",
        "동 이름 대신 읍 이름으로 검색해도 됩니까?",
        "본인 인증 번호가 만료되면 새로 받을 수 있을까요?",
        "증명서 비밀번호 변경 메뉴는 어디에 있습니까?",
        "인증 코드 재전송은 몇 번까지 가능한가요?",
        "대형폐기물 확인 번호가 만료되었다고 나옵니다.",
        "비번을 바꾼 뒤 이전 신청을 확인할 수 있습니까?",
        "인증번호 재요청 버튼이 작동하지 않습니다.",
        "본인 인증용 확인 번호를 언제 입력합니까?",
        "신고서 이름을 수정하면 접수번호가 바뀝니까?",
        "신청자 성함 표기를 지우는 방법이 있습니까?",
        "전입신고서의 도로명 주소 항목은 반드시 작성해야 합니까?",
        "수거 안내용 휴대전화 연락처를 삭제할 수 있습니까?",
        "폐기물 신고용 암호 변경은 어디에서 처리합니까?",
        "지방세 안내문 수령지를 온라인으로 정정할 수 있습니까?",
    ],
)
def test_adjacent_p0_question_remains_safe_unchanged(raw: str) -> None:
    result = redact_question(raw)

    assert result.masked_text == raw
    assert result.findings == ()
    assert result.safe_for_failure_storage is True
    assert result.safe_for_synthetic_provider is True
    assert result.unresolved_reason is None


@pytest.mark.parametrize(
    "raw",
    [
        "주소는 어디에서 수정할 수 있습니까?",
        "성명 표기 원칙을 알고 싶습니다.",
        "신청인 성명을 바로잡는 절차가 궁금합니다.",
        "이름이 거꾸로 표시됩니다.",
        "성명 표기가 깨져 보여요.",
        "비밀번호는 보안을 위해 주기적으로 바꾸는 것이 좋습니까?",
        "인증 코드는 시스템에서 언제 폐기됩니까?",
    ],
)
def test_unseen_valueless_grammar_remains_safe_unchanged(raw: str) -> None:
    result = redact_question(raw)

    assert result == type(result)(raw, (), True, True, None)


def test_pregnancy_week_is_masked_without_name_false_positive() -> None:
    raw = "현재 임신 12주예요."
    result = redact_question(raw)

    assert result.masked_text == "현재 [건강·복지정보]예요."
    assert [finding.category for finding in result.findings] == [
        PiiCategory.SENSITIVE_HEALTH_WELFARE
    ]
    assert result.safe_for_failure_storage is True
    assert result.safe_for_synthetic_provider is True
    assert result.unresolved_reason is None
