// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import AdminPage from "./page";

describe("admin page", () => {
  afterEach(() => {
    delete process.env.ADMIN_UI_ENABLED;
    delete process.env.ADMIN_UI_MODE;
    vi.unstubAllGlobals();
  });

  it("selects actual API transport only when the server explicitly requests actual mode", () => {
    process.env.ADMIN_UI_ENABLED = "true";
    process.env.ADMIN_UI_MODE = "actual";
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0 }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    ));

    render(<AdminPage />);

    expect(screen.getByText("실제 local DB API 연결")).toBeInTheDocument();
    expect(screen.queryByText("시연용 샘플 데이터")).not.toBeInTheDocument();
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
    process.env.ADMIN_UI_MODE = "actual";
    expect(() => AdminPage()).toThrow(/NEXT_HTTP_ERROR_FALLBACK;404/);
  });
});
