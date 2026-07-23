// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ChatPage from "./page";

describe("chat page", () => {
  it("exposes the citizen chat landmarks and form", () => {
    render(<ChatPage />);

    expect(screen.getByRole("heading", { level: 1, name: "민원을 물어보세요" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    expect(screen.getByRole("link", { name: "본문 바로가기" })).toHaveAttribute(
      "href",
      "#main-content",
    );
    expect(screen.getByRole("textbox", { name: "민원 질문" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "지역 선택" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "질문 보내기" })).toBeDisabled();
    expect(screen.getByText("아직 대화가 없어요.")).toBeInTheDocument();
  });
});
