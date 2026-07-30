import type { components } from "../../../../packages/shared-contracts/src/generated/api";

type FailedQuestion = components["schemas"]["FailedQuestion"];

/**
 * 서버가 예약해 둔 KB-WASTE-03 활성화 후보의 공식 값이다.
 *
 * `apps/api/src/sejong_ai_api/admin/candidate_binding.py` 의 상수와 **정확히 일치**해야 한다.
 * 한 글자라도 다르면 승인은 200으로 성공하지만 KB가 활성화되지 않아
 * 같은 질문을 다시 물었을 때 계속 폴백한다.
 *
 * 값의 유일한 출처는 위 서버 모듈이다. 미승인 초안 데이터의 문구는 이 상수와 다르므로
 * 그것을 근거로 값을 바꾸지 않는다.
 */
export type ReservedCandidateDraft = Readonly<{
  representativeQuestion: string;
  title: string;
  answerSummary: string;
  procedureSteps: readonly string[];
  requiredDocuments: readonly string[];
  processingTime: string;
  fee: string;
  department: string;
  sourceTitle: string;
  sourceUrl: string;
  lastVerifiedAt: string;
  caution: string;
}>;

export const RESERVED_CANDIDATE: ReservedCandidateDraft = {
  representativeQuestion: "침대 2인용 프레임 수수료가 얼마예요?",
  title: "침대 프레임 배출 수수료",
  answerSummary:
    "공식 품목표의 침대 프레임 수수료는 1인용침대 8,000원, 2인용침대 10,000원으로 표시됩니다.",
  procedureSteps: [
    "공식 품목표에서 침대 프레임의 1인용침대 또는 2인용침대 항목을 확인합니다.",
    "해당 수수료로 공식 배출 절차를 진행합니다.",
  ],
  requiredDocuments: [],
  processingTime: "",
  fee: "1인용침대 8,000원; 2인용침대 10,000원",
  department: "세종특별자치시시설관리공단",
  sourceTitle: "배출항목선택",
  sourceUrl: "https://www.sjwaste.kr/wasteApp/appCategoryPopup.do?menuId=MENU00305",
  lastVerifiedAt: "2026-07-18",
  caution:
    "공식 품목표의 1인용침대·2인용침대 항목을 그대로 따릅니다. " +
    "매트리스 포함 가격이나 실제 규격을 단정하지 않습니다.",
};

/**
 * 이 실패 질문이 예약된 활성화 대상인지 판정한다.
 *
 * 마스킹 질문이 예약 대표질문과 정확히 같고 분야가 대형폐기물일 때만 참이다.
 * 운영자는 채워진 값을 그대로 승인 요청하거나 직접 수정할 수 있으며,
 * 최종 판정은 언제나 별도 승인자가 한다.
 */
export function isReservedCandidateTarget(failure: FailedQuestion): boolean {
  return (
    failure.intent === "BULKY_WASTE" &&
    failure.masked_question === RESERVED_CANDIDATE.representativeQuestion
  );
}
