// @vitest-environment jsdom

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ChatPreparationPage from "./page";

describe("chat preparation page", () => {
  it("presents a single static preparation page with the approved scope", () => {
    render(<ChatPreparationPage />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "민원 안내 채팅을 준비하고 있습니다.",
    );
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    expect(screen.getByRole("link", { name: "본문 바로가기" })).toHaveAttribute(
      "href",
      "#main-content",
    );

    const scope = screen.getByRole("region", { name: "준비 중인 지원 분야" });
    expect(within(scope).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "전입·주민등록",
      "증명서 발급",
      "대형폐기물",
      "지방세 일반 안내",
    ]);
  });

  it("states limits and exposes no data-collection controls", () => {
    const { container } = render(<ChatPreparationPage />);

    expect(
      screen.getByText(
        "채팅 답변, 민원 신청, 개인별 조회와 공식 KB 데이터는 아직 제공하지 않습니다.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "소개 화면으로 돌아가기" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(container.querySelector("form, input, textarea, select, button")).toBeNull();
  });
});
