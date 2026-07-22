// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import AdminPage from "./page";

describe("admin page", () => {
  afterEach(() => {
    delete process.env.ADMIN_UI_ENABLED;
  });

  it("exposes the local/private operations route with a keyboard skip link", () => {
    process.env.ADMIN_UI_ENABLED = "true";
    render(<AdminPage />);

    expect(screen.getByRole("heading", { name: "AI 민원 운영센터" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "본문 바로가기" })).toHaveAttribute("href", "#admin-main");
    expect(screen.getByText("local/private 관리자 시연")).toBeInTheDocument();
    expect(screen.getByText("시연용 샘플 데이터")).toBeInTheDocument();
  });

  it("keeps the administrator route closed unless the server explicitly enables it", () => {
    expect(() => AdminPage()).toThrow(/NEXT_HTTP_ERROR_FALLBACK;404/);
  });
});
