// @vitest-environment jsdom

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("home page shell", () => {
  it("presents the service identity and principle with exactly one main heading", () => {
    render(<Home />);

    expect(screen.getByText("세종 민원 AI 길잡이", { exact: true })).toBeInTheDocument();

    const mainHeadings = screen.getAllByRole("heading", { level: 1 });
    expect(mainHeadings).toHaveLength(1);
    expect(mainHeadings[0]).toHaveTextContent(
      "모르면 지어내지 않고, 알면 끝까지 안내",
    );
  });

  it("provides skip and in-page supported-service links without a dead chat route", () => {
    const { container } = render(<Home />);

    expect(screen.getByRole("link", { name: "본문 바로가기" })).toHaveAttribute(
      "href",
      "#main-content",
    );
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    expect(
      screen.getByRole("link", { name: "지원 분야 확인하기" }),
    ).toHaveAttribute("href", "#supported-services");
    expect(container.querySelector('a[href="/chat"]')).not.toBeInTheDocument();
  });

  it("lists the four approved service areas in a semantic section", () => {
    const { container } = render(<Home />);
    const section = container.querySelector("section#supported-services");

    expect(section).not.toBeNull();
    expect(section).toHaveAttribute("aria-labelledby", "supported-services-title");
    expect(
      within(section as HTMLElement).getByRole("heading", { name: "지원 분야" }),
    ).toHaveAttribute("id", "supported-services-title");

    const items = within(section as HTMLElement).getAllByRole("listitem");
    expect(items).toHaveLength(4);
    expect(items.map((item) => item.textContent)).toEqual([
      "전입·주민등록",
      "증명서 발급",
      "대형폐기물",
      "지방세 일반 안내",
    ]);
  });

  it("states the current development limits and exposes semantic landmarks", () => {
    render(<Home />);

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(
      screen.getByText("현재는 서비스 소개 화면을 준비한 개발 단계입니다."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "채팅 답변, 민원 신청, 개인 조회와 공식 KB 데이터는 아직 제공하지 않습니다.",
      ),
    ).toBeInTheDocument();
  });
});
