# WEB-HOME-001: Home CTA and Static Chat Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the home-page entry flow by linking `/` to an accessible, static `/chat` preparation shell that truthfully describes the four approved support areas and its current limits without collecting or transmitting anything.

**Architecture:** Keep both routes as Next.js App Router Server Components. Reuse the existing global semantic, mobile-first visual foundation and add only static markup and CSS; `/chat` has no client component, state, form control, request, storage, cookie, API, LLM, or official-data dependency. Add render tests first, then a production-browser Playwright gate for navigation, privacy boundary, responsive layout, focus, and contrast evidence.

**Tech Stack:** Next.js 16.2.10, React 19.2.7, TypeScript 5.9.3, Tailwind CSS 4.3.2 local CSS, Vitest 4.1.10 + Testing Library, and dev-only `@playwright/test` 1.61.1.

## Global Constraints

- Q-WEB-001=A is explicitly approved: create a minimal static `/chat` preparation route and link the home CTA to it; no dead `/chat` link remains.
- Preserve exactly these four support areas, in this order: `전입·주민등록`, `증명서 발급`, `대형폐기물`, `지방세 일반 안내`.
- State plainly that chat answers, civil-application submission, individual lookup, and official KB data are not yet available; never imply that the preparation shell can answer a question.
- Do not add a form, input, textarea, select, submit button, fetch/XHR/WebSocket request, API route, browser storage, cookie, analytics, LLM call, official data, mock data, external font, image, script, or other external asset.
- Keep `/`, `/chat`, and `/admin` as the only product route names; this task creates only `/chat` and does not implement `/admin` or WEB-CHAT-001 conversational behavior.
- Use semantic landmarks, exactly one `h1` per route, a visible keyboard focus indicator, body contrast of at least 4.5:1, and the existing Korean system-font stack.
- Verify 390px, 430px, and desktop viewports with no horizontal overflow; verify keyboard navigation and focus in a real production browser.
- No public API, OpenAPI/schema, database migration, database seed, official/mock-data version, environment variable, cookie, or deployment change is allowed.
- Use Node `24.12.0` and pnpm `11.13.0`; all package changes must be exact-versioned and locked by the root `pnpm-lock.yaml`.
- Create the required implementation note, index row, TASKS row update, changelog entry, and version-manifest update as part of the final documentation task.

---

## Current State and Decision Boundary

- `apps/web/src/app/page.tsx` already has a static, semantic home page, four approved areas, truthful development limits, an in-page `지원 분야 확인하기` link, and an explicit test that no `/chat` link exists.
- `apps/web/src/app/chat/` does not exist, so adding a `/chat` link before adding the route would produce a 404.
- `apps/web/src/app/globals.css` already supplies system fonts, 18px base text, contrast-safe tokens, skip-link behavior, focus styling, and responsive `.service-grid` breakpoints.
- `apps/web/package.json` has Vitest/Testing Library but no direct browser-test runner. The root lock contains only optional Playwright peer metadata; it is not an installed test tool.
- `PLAN-20260714-001-foundation-and-governed-chat.md` already approved Playwright and axe-class tooling as development/test dependencies. This task needs repeatable viewport, navigation, focus, and network/privacy checks that JSDOM cannot make, so install only the already-approved dev dependency `@playwright/test@1.61.1`; do not install `axe-core` or any runtime package in this slice. Version `1.61.1` was verified on 2026-07-19 against the Microsoft-published npm registry metadata; it supports Node `>=18`, and the official Playwright system requirements list current Node 24.x.
- This is independent of DATA-SEED-001. The static wording must not read staging data, official data, or the pending approval manifest and must leave `/ready=503` unchanged.

## File Structure

| File | Action | Responsibility |
| --- | --- | --- |
| `apps/web/src/app/chat/page.test.tsx` | Create | JSDOM contract for the static `/chat` content, landmarks, list, limits, and absence of form controls. |
| `apps/web/src/app/chat/page.tsx` | Create | Server-rendered preparation shell with no behavioral code or data access. |
| `apps/web/src/app/page.test.tsx` | Modify | Replace the obsolete no-`/chat` assertion with an accessible CTA destination assertion. |
| `apps/web/src/app/page.tsx` | Modify | Point the sole primary home CTA to `/chat`; preserve the supported-services section and all approved wording. |
| `apps/web/src/app/globals.css` | Modify | Style the static chat shell with the existing tokens, focus treatment, and mobile-first layout. |
| `apps/web/e2e/home-chat-shell.spec.ts` | Create | Production-browser checks for navigation, responsive widths, landmarks/focus, no form/storage/cookie/API/external request, and text contrast. |
| `apps/web/playwright.config.ts` | Create | Local loopback production-server configuration and three browser projects. |
| `apps/web/package.json` | Modify | Add exact dev-only Playwright package and `test:e2e` script; no production dependency changes. |
| `pnpm-lock.yaml` | Modify | Frozen lock resolution for the exact approved dev-only package. |
| `apps/web/README.md` | Modify | Correct the route inventory and static privacy boundary. |
| `TASKS.md` | Modify | Mark WEB-HOME-001 Done only after all listed gates pass and link its implementation note. |
| `CHANGELOG.md` | Modify | Add the static `/chat` shell and its browser verification under Unreleased. |
| `versions/manifest.json` | Modify | Advance only application, web, test-suite, and documentation patch axes. |
| `docs/implementation-notes/IMP-20260719-005-web-home과-정적-채팅-준비-화면.md` | Modify | Reproducible 6W1H record with commands, browser evidence, privacy statement, rollback, and human/AI boundary. |
| `docs/implementation-notes/INDEX.md` | Modify | Add the implementation-note row. |

## Interfaces

No public API or data contract changes are introduced. The approved user-visible route/CTA behavior
does change by D-037/Q-WEB-001.

- `/` produces a native anchor named `민원 안내 시작하기` with `href="/chat"`.
- `/chat` is a server-rendered `200` page containing static Korean copy only.
- Neither route accepts input or emits an API request; later WEB-CHAT-001 may replace the shell only after API-CHAT-001 and its data/privacy gates are complete.

## Task 1: Define and Implement the Static `/chat` Route

**Files:**

- Create: `apps/web/src/app/chat/page.test.tsx`
- Create: `apps/web/src/app/chat/page.tsx`

**Consumes:** Existing `apps/web/src/test/setup.ts`, global layout, and the approved four-area scope.

**Produces:** A static Server Component at `/chat` whose copy and semantics are consumed by the home CTA and browser test.

- [ ] **Step 1: Write the failing render test for the preparation shell.**

```tsx
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
```

- [ ] **Step 2: Run the test to verify RED.**

Run: `corepack.cmd pnpm --filter @sejong-ai/web test -- src/app/chat/page.test.tsx`

Expected: FAIL because `apps/web/src/app/chat/page.tsx` does not exist.

- [ ] **Step 3: Add the smallest static Server Component that satisfies the contract.**

```tsx
const supportedServices = [
  "전입·주민등록",
  "증명서 발급",
  "대형폐기물",
  "지방세 일반 안내",
] as const;

export default function ChatPreparationPage() {
  return (
    <>
      <a className="skip-link" href="#main-content">
        본문 바로가기
      </a>

      <header className="site-header">
        <div className="page-shell">
          <a className="service-name" href="/">
            세종 민원 AI 길잡이
          </a>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <section className="chat-shell" aria-labelledby="chat-page-title">
          <div className="page-shell chat-shell-content">
            <p className="eyebrow">안전한 안내를 위한 준비 단계</p>
            <h1 id="chat-page-title">민원 안내 채팅을 준비하고 있습니다.</h1>
            <p className="chat-summary">
              승인된 공식 근거를 확인한 뒤, 알 수 있는 내용만 끝까지 안내하겠습니다.
            </p>

            <aside className="development-notice" aria-labelledby="chat-limit-title">
              <p className="notice-label" id="chat-limit-title">
                현재 제공하지 않는 기능
              </p>
              <p>
                채팅 답변, 민원 신청, 개인별 조회와 공식 KB 데이터는 아직 제공하지 않습니다.
              </p>
            </aside>

            <section className="chat-scope" aria-labelledby="chat-scope-title">
              <p className="section-kicker">준비 중인 범위</p>
              <h2 id="chat-scope-title">준비 중인 지원 분야</h2>
              <ul className="chat-info-grid">
                {supportedServices.map((service) => (
                  <li key={service}>{service}</li>
                ))}
              </ul>
            </section>

            <a className="secondary-link" href="/">
              소개 화면으로 돌아가기
            </a>
          </div>
        </section>
      </main>
    </>
  );
}
```

Do not add `"use client"`, imports other than React types, event handlers, form fields, cookies, state, storage, network code, or data imports.

- [ ] **Step 4: Run the focused test to verify GREEN.**

Run: `corepack.cmd pnpm --filter @sejong-ai/web test -- src/app/chat/page.test.tsx`

Expected: PASS with `2 passed`.

- [ ] **Step 5: Review the route boundary before continuing.**

Run: `rg -n "use client|fetch\(|XMLHttpRequest|WebSocket|localStorage|sessionStorage|indexedDB|document\.cookie|<form|<input|<textarea|<select|<button" apps/web/src/app/chat/page.tsx`

Expected: exit code `1` with no matches. This is a scoped source check; the browser gate in Task 3 remains required.

- [ ] **Step 6: Commit the independently testable route slice.**

Run:

```powershell
git add apps/web/src/app/chat/page.tsx apps/web/src/app/chat/page.test.tsx
git commit -m "feat(web): add static chat preparation shell"
```

Expected: one commit containing only the new route and render test.

## Task 2: Connect the Home CTA Without Changing Scope or Claims

**Files:**

- Modify: `apps/web/src/app/page.test.tsx`
- Modify: `apps/web/src/app/page.tsx`

**Consumes:** The `/chat` route from Task 1 and existing semantic home shell.

**Produces:** One native home CTA that reaches the existing `/chat` route; it preserves the four-area section and current limits.

- [ ] **Step 1: Replace the obsolete no-route assertion with a failing CTA contract.**

Replace the second test in `apps/web/src/app/page.test.tsx` with:

```tsx
  it("provides skip and chat-entry links without removing the supported-services link", () => {
    render(<Home />);

    expect(screen.getByRole("link", { name: "본문 바로가기" })).toHaveAttribute(
      "href",
      "#main-content",
    );
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
    expect(screen.getByRole("link", { name: "민원 안내 시작하기" })).toHaveAttribute(
      "href",
      "/chat",
    );
    expect(screen.getByRole("link", { name: "지원 분야 확인하기" })).toHaveAttribute(
      "href",
      "#supported-services",
    );
  });
```

- [ ] **Step 2: Run the focused test to verify RED.**

Run: `corepack.cmd pnpm --filter @sejong-ai/web test -- src/app/page.test.tsx`

Expected: FAIL because `민원 안내 시작하기` is not rendered.

- [ ] **Step 3: Change only the CTA portion of the home hero.**

Replace the existing primary anchor in `apps/web/src/app/page.tsx` with the following two anchors, leaving the existing development notice and supported-services section unchanged:

```tsx
            <a className="primary-link" href="/chat">
              민원 안내 시작하기
            </a>
            <a className="text-link" href="#supported-services">
              지원 분야 확인하기
            </a>
```

The CTA must remain a native anchor rather than a button so keyboard activation and destination semantics are native. Do not alter the `supportedServices` array, the four service labels, or the development-limit text.

- [ ] **Step 4: Run the home and chat render tests to verify GREEN.**

Run: `corepack.cmd pnpm --filter @sejong-ai/web test -- src/app/page.test.tsx src/app/chat/page.test.tsx`

Expected: PASS with `6 passed`.

- [ ] **Step 5: Commit the navigable home slice.**

Run:

```powershell
git add apps/web/src/app/page.tsx apps/web/src/app/page.test.tsx
git commit -m "feat(web): link home CTA to chat preparation"
```

Expected: one commit containing only the CTA and its test change.

## Task 3: Add Responsive Styling and Production-Browser Tests

**Files:**

- Modify: `apps/web/src/app/globals.css`
- Create: `apps/web/e2e/home-chat-shell.spec.ts`
- Create: `apps/web/playwright.config.ts`
- Modify: `apps/web/package.json`
- Modify: `pnpm-lock.yaml`

**Consumes:** Static route/CTA markup from Tasks 1 and 2 plus existing color tokens and base focus rule.

**Produces:** Repeatable Chromium validation at 390px, 430px, and desktop; a local-only test runner; scoped responsive styles with no external asset or runtime behavior.

- [ ] **Step 1: Add the exact dev-only browser test dependency and script.**

Change only the following `apps/web/package.json` entries:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:e2e": "playwright test"
  },
  "devDependencies": {
    "@playwright/test": "1.61.1"
  }
}
```

Merge the shown entries into the existing object; retain every existing exact dependency version. Then generate only the lock update:

Run: `corepack.cmd pnpm add --filter @sejong-ai/web --save-dev --save-exact @playwright/test@1.61.1`

Expected: `apps/web/package.json` and root `pnpm-lock.yaml` change; no `dependencies` entry changes. Review the diff before any browser download.

- [ ] **Step 2: Create the local production-server configuration.**

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3001",
    browserName: "chromium",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "corepack.cmd pnpm --filter @sejong-ai/web start -- --hostname 127.0.0.1 --port 3001",
    url: "http://127.0.0.1:3001",
    reuseExistingServer: false,
    timeout: 120_000,
  },
  projects: [
    { name: "mobile-390", use: { viewport: { width: 390, height: 844 } } },
    { name: "mobile-430", use: { viewport: { width: 430, height: 932 } } },
    { name: "desktop", use: { viewport: { width: 1440, height: 900 } } },
  ],
});
```

- [ ] **Step 3: Write the browser tests before adding chat-specific CSS.**

```ts
import { expect, test } from "@playwright/test";

const allowedServices = [
  "전입·주민등록",
  "증명서 발급",
  "대형폐기물",
  "지방세 일반 안내",
];

test("home CTA reaches the static chat shell by keyboard", async ({ page }) => {
  await page.goto("/");
  const entry = page.getByRole("link", { name: "민원 안내 시작하기" });
  await entry.focus();
  await expect(entry).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/chat$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "민원 안내 채팅을 준비하고 있습니다.",
  );
});

test("chat shell has the static privacy boundary and approved visible scope", async ({ page }) => {
  const requests: string[] = [];
  page.on("request", (request) => requests.push(request.url()));

  await page.goto("/chat");
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("region", { name: "준비 중인 지원 분야" }).getByRole("listitem")).toHaveText(
    allowedServices,
  );
  await expect(page.locator("form, input, textarea, select, button")).toHaveCount(0);
  await expect(page.getByText("채팅 답변, 민원 신청, 개인별 조회와 공식 KB 데이터는 아직 제공하지 않습니다.")).toBeVisible();

  expect(await page.context().cookies()).toEqual([]);
  expect(
    await page.evaluate(async () => ({
      indexedDbCount: (await indexedDB.databases()).length,
      localStorageCount: localStorage.length,
      sessionStorageCount: sessionStorage.length,
    })),
  ).toEqual({ indexedDbCount: 0, localStorageCount: 0, sessionStorageCount: 0 });

  const requestOrigins = requests.map((requestUrl) => new URL(requestUrl).origin);
  expect(requestOrigins.every((origin) => origin === "http://127.0.0.1:3001")).toBe(true);
  expect(requests.filter((requestUrl) => new URL(requestUrl).pathname.startsWith("/api/")).toEqual([]);
});

test("chat shell fits the viewport and retains focus and readable contrast", async ({ page }) => {
  await page.goto("/chat");

  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth),
  ).toBe(true);
  await expect(page.locator(".chat-info-grid")).toHaveCSS("display", "grid");

  const homeLink = page.getByRole("link", { name: "소개 화면으로 돌아가기" });
  await homeLink.focus();
  await expect(homeLink).toBeFocused();
  const focusStyle = await homeLink.evaluate((element) => {
    const style = getComputedStyle(element);
    return { outlineStyle: style.outlineStyle, boxShadow: style.boxShadow };
  });
  expect(focusStyle.outlineStyle !== "none" || focusStyle.boxShadow !== "none").toBe(true);

  const ratio = await page.locator(".chat-summary").evaluate((element) => {
    const parse = (value: string) => value.match(/\d+/g)!.slice(0, 3).map(Number) as [number, number, number];
    const color = parse(getComputedStyle(element).color);
    const background = parse(getComputedStyle(document.body).backgroundColor);
    const luminance = (rgb: [number, number, number]) => {
      const linear = rgb.map((channel) => {
        const value = channel / 255;
        return value <= 0.03928 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };
    const [lighter, darker] = [luminance(color), luminance(background)].sort((a, b) => b - a);
    return (lighter + 0.05) / (darker + 0.05);
  });
  expect(ratio).toBeGreaterThanOrEqual(4.5);
});
```

The in-page contrast evaluator is deliberately self-contained because Playwright cannot serialize a closure. With `.chat-info-grid` currently unstyled, the third test must first fail on its `display: grid` assertion.

- [ ] **Step 4: Run the browser suite to verify RED.**

Run:

```powershell
corepack.cmd pnpm --filter @sejong-ai/web build
corepack.cmd pnpm --filter @sejong-ai/web exec playwright install chromium
corepack.cmd pnpm --filter @sejong-ai/web test:e2e
```

Expected: first two commands succeed; all three viewport projects fail the third test because `.chat-info-grid` has no `display: grid` style. Do not accept an accidental pass by weakening that assertion.

- [ ] **Step 5: Add the exact scoped CSS.**

Append these rules after the existing `.service-grid` rules and before the existing reduced-motion media query:

```css
.text-link {
  width: fit-content;
  color: var(--accent-strong);
  font-weight: 800;
}

.chat-shell {
  padding-block: clamp(3rem, 9vw, 6.5rem);
}

.chat-shell-content {
  display: grid;
  gap: 1.5rem;
}

.chat-shell h1 {
  max-width: 16ch;
  margin-bottom: 0;
  font-size: clamp(2.25rem, 9vw, 4.25rem);
  line-height: 1.16;
  letter-spacing: -0.045em;
  text-wrap: balance;
}

.chat-summary {
  max-width: 42rem;
  margin-bottom: 0;
  color: var(--text-muted);
  font-size: clamp(1.125rem, 3vw, 1.3rem);
}

.chat-scope {
  display: grid;
  gap: 0.75rem;
  max-width: 60rem;
}

.chat-scope h2 {
  margin-bottom: 0;
  font-size: clamp(1.75rem, 6vw, 2.75rem);
  line-height: 1.2;
  letter-spacing: -0.035em;
}

.chat-info-grid {
  display: grid;
  gap: 0.75rem;
  margin: 0.75rem 0 0;
  padding: 0;
  list-style: none;
}

.chat-info-grid li {
  min-width: 0;
  padding: 1.125rem;
  border: 0.125rem solid var(--border);
  border-radius: 0.75rem;
  background: var(--surface-muted);
  color: var(--text);
  font-weight: 800;
}

.secondary-link {
  display: inline-flex;
  width: fit-content;
  min-height: 3.25rem;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.25rem;
  border: 0.125rem solid var(--accent);
  border-radius: 0.75rem;
  background: var(--surface);
  color: var(--accent-strong);
  font-weight: 800;
  text-decoration: none;
}

.secondary-link:hover {
  border-color: var(--accent-strong);
  background: var(--surface-muted);
  color: var(--accent-strong);
}

@media (min-width: 34rem) {
  .chat-info-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 64rem) {
  .chat-info-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
```

The existing token values are retained: `--text-muted: #3f4d66` on `--background: #f4f7fb`, `--accent-strong: #063b88` on white, and white on `--accent: #084fb7`. The browser test independently verifies the normal body-text ratio; manually record the computed ratios for the remaining link/button combinations in the implementation note.

- [ ] **Step 6: Run unit, type, lint, build, and browser GREEN gates.**

Run:

```powershell
corepack.cmd pnpm --filter @sejong-ai/web test
corepack.cmd pnpm --filter @sejong-ai/web typecheck
corepack.cmd pnpm --filter @sejong-ai/web lint
corepack.cmd pnpm --filter @sejong-ai/web build
corepack.cmd pnpm --filter @sejong-ai/web test:e2e
```

Expected: Vitest `6 passed`; typecheck/lint/build exit `0`; Playwright `9 passed` (three tests in each of 390, 430, and desktop projects). Test artifacts are local/transient and must not be committed.

- [ ] **Step 7: Perform the required manual browser QA against the production server.**

For each viewport (390×844, 430×932, 1440×900), visit `/` and `/chat` on `http://127.0.0.1:3001` and record in the note:

1. no horizontal scrollbar or clipped card/link;
2. visible skip link after `Tab`, then focus lands on `main` after activation;
3. visible focus ring for `민원 안내 시작하기`, service-name home link, and `소개 화면으로 돌아가기`;
4. Enter opens `/chat`, and the return link opens `/`;
5. heading/list reading order is understandable at 200% browser zoom;
6. browser console has no error/warning and Network has no `/api/` or third-party request.

- [ ] **Step 8: Commit the styling, browser configuration, and lockfile together.**

Run:

```powershell
git add apps/web/src/app/globals.css apps/web/e2e/home-chat-shell.spec.ts apps/web/playwright.config.ts apps/web/package.json pnpm-lock.yaml
git commit -m "test(web): verify static home chat entry in browser"
```

Expected: one commit with dev-only test tooling, no runtime package change, and no generated browser binary/artifact.

## Task 4: Synchronize Documentation, Version Axes, and Handoff Evidence

**Files:**

- Modify: `apps/web/README.md`
- Modify: `TASKS.md`
- Modify: `CHANGELOG.md`
- Modify: `versions/manifest.json`
- Modify: `docs/implementation-notes/IMP-20260719-005-web-home과-정적-채팅-준비-화면.md`
- Modify: `docs/implementation-notes/INDEX.md`

**Consumes:** Actual Task 1–3 command outputs, browser screenshots only if a failure requires retention, and exact final Git commit IDs.

**Produces:** A reproducible project record; no product behavior.

- [ ] **Step 1: Update the Web README’s current-scope statements.**

Replace the first paragraph and current-behavior bullets with this exact content:

```md
세종 민원 AI 길잡이의 Next.js 웹 앱이다. 현재 구현 범위는 정적 소개 화면 `/`와 입력·저장 없는 `/chat` 준비 화면이며, 승인된 공식 KB를 사용하는 대화와 local/private 전용 `/admin`은 후속 수직 흐름에서 구현한다.

## 현재 동작

- 서비스명과 핵심 원칙을 소개한다.
- 승인된 네 지원 분야와 현재 제공하지 않는 기능을 안내한다.
- 홈의 `민원 안내 시작하기`는 404가 아닌 정적 `/chat` 준비 화면으로 이동한다.
- `/chat`에는 채팅 입력, 민원 신청, 개인 조회, 공식 KB 데이터, API 호출, 브라우저 저장소, 쿠키, 분석 도구, 외부 폰트·이미지가 없다.
- 두 화면 모두 키보드 본문 건너뛰기와 보이는 포커스 표시를 제공한다.
```

- [ ] **Step 2: Update the task, changelog, and version records with the actual evidence.**

Make these bounded changes only after every Task 3 gate is green:

```md
| WEB-HOME-001 | P0 | Frontend·QA | `/` 서비스 소개·4개 지원 분야·한계·`/chat` 진입 | Done | DEV-001 complete; Q-WEB-001=A | static `/chat` route, home CTA, 390/430/desktop keyboard·focus·contrast·privacy browser gate, [IMP-20260719-005](docs/implementation-notes/IMP-20260719-005-web-home과-정적-채팅-준비-화면.md) |
```

Add this `CHANGELOG.md` Unreleased/Added bullet:

```md
- WEB-HOME-001 static `/chat` preparation shell, navigable home CTA, no-input/no-storage/no-request browser guard, and 390/430/desktop accessibility verification
```

Set only these manifest values, preserving all other axes and replacing `updated_at` with the actual KST completion time:

```json
"application": "0.2.0",
"web": "0.2.0-static-chat-shell",
"test_suite": "0.8.0-web-browser-gate",
"documentation": "2.7.0"
```

- [ ] **Step 3: Create the implementation note from the repository template with complete evidence.**

Complete `docs/implementation-notes/IMP-20260719-005-web-home과-정적-채팅-준비-화면.md` using `docs/implementation-notes/TEMPLATE.md` and fill every heading. It must state all of the following concrete facts:

```md
- Task ID: WEB-HOME-001; status Done only if all Task 3 commands passed.
- Decision: Q-WEB-001=A; a static `/chat` shell was chosen to prevent the prior 404 while API-CHAT-001 and WEB-CHAT-001 remain unimplemented.
- Scope: exactly four areas, no form/input/fetch/storage/cookie/API/LLM/official or mock data/external asset.
- Versions: application 0.1.0→0.2.0, web 0.1.0→0.2.0-static-chat-shell, test suite 0.7.0-data-trust-boundary→0.8.0-web-browser-gate, documentation 2.6.1→2.7.0; API, DB, official data, mock data, and prompt set unchanged.
- Dependencies: `@playwright/test@1.61.1` is dev-only, pre-approved by PLAN-001, exact-locked, and Chromium is a local test artifact; no production dependency was added.
- Evidence: exact Vitest/typecheck/lint/build/Playwright commands, pass counts, viewport dimensions, manual keyboard/zoom/console/network checks, and `git diff --check` result.
- Privacy/security: no raw question exists in either page; no request/storage/cookie/data/provider path is present; public deployment remains blocked by Q-SEC-003/A-021.
- Rollback: `git revert` the three WEB-HOME commits in reverse order; this restores the prior no-`/chat`-link state without DB/data/API cleanup.
- Remaining risk: the preparation shell is intentionally not a chat product; WEB-CHAT-001 cannot add a form or network call until API-CHAT-001, ACTIVE seed/readiness, and its own privacy/accessibility plan are complete.
```

Add this exact index-row shape to `docs/implementation-notes/INDEX.md`, replacing the three version values with the final actual values only if a prior task changed them:

```md
| [IMP-20260719-005](IMP-20260719-005-web-home과-정적-채팅-준비-화면.md) | 2026-07-19 | WEB-HOME-001 | implementation | 홈 CTA와 입력·저장 없는 정적 `/chat` 준비 화면, mobile/desktop browser gate | app 0.1.0→0.2.0; web 0.1.0→0.2.0; tests 0.7.0→0.8.0; docs 2.6.1→2.7.0 | Done |
```

- [ ] **Step 4: Run final quality, safety, and documentation checks.**

Run:

```powershell
corepack.cmd pnpm install --frozen-lockfile --ignore-scripts
corepack.cmd pnpm --filter @sejong-ai/web test
corepack.cmd pnpm --filter @sejong-ai/web typecheck
corepack.cmd pnpm --filter @sejong-ai/web lint
corepack.cmd pnpm --filter @sejong-ai/web build
corepack.cmd pnpm --filter @sejong-ai/web test:e2e
node scripts/check_web_bundle_secrets.mjs apps/web/.next
git diff --check
git status --short
```

Expected: frozen install and every Web gate exit `0`; the browser-secret scan reports zero findings; `git diff --check` is silent; status contains only the intended tracked source, test, lock, and documentation files before committing.

- [ ] **Step 5: Self-review the exact requirements before the documentation commit.**

Confirm each statement against the final diff:

| Requirement | Evidence |
| --- | --- |
| Q-WEB-001=A route and CTA | `/chat` page exists; home `민원 안내 시작하기` has `/chat`; Playwright Enter navigation passes. |
| Four-area scope | Both render tests assert the exact ordered four-item list. |
| Clear limits | Home and chat render tests assert the exact unavailable-features sentence. |
| No input or collection | Static-source deny scan plus browser count/storage/cookie/API/origin assertions pass. |
| Responsive and accessible | Three browser projects, no-overflow check, native landmarks/headings, Tab/Enter/focus and 200% manual QA pass. |
| No external asset/API/LLM/data change | Request-origin/API assertions, diff review, and unchanged contract/database/data paths prove the boundary. |
| Version/note synchronization | README, TASKS, changelog, manifest, implementation note, and index are all in the final diff. |

- [ ] **Step 6: Commit the documentation and version synchronization.**

Run:

```powershell
git add apps/web/README.md TASKS.md CHANGELOG.md versions/manifest.json docs/implementation-notes/IMP-20260719-005-web-home과-정적-채팅-준비-화면.md docs/implementation-notes/INDEX.md
git commit -m "docs: record WEB-HOME-001 completion"
```

Expected: one documentation-only commit after all quality gates are green.

## Complete Verification Matrix

| Layer | Command or check | Expected evidence |
| --- | --- | --- |
| Unit render | `corepack.cmd pnpm --filter @sejong-ai/web test` | `6 passed`; both routes have one h1, semantic landmarks, exact four areas, limits, native links, and no chat form controls. |
| Type | `corepack.cmd pnpm --filter @sejong-ai/web typecheck` | Exit `0`; Playwright config/spec and Server Components type-check. |
| Lint | `corepack.cmd pnpm --filter @sejong-ai/web lint` | Exit `0`; no unused browser-test helper or invalid JSX. |
| Build | `corepack.cmd pnpm --filter @sejong-ai/web build` | Exit `0`; `/` and `/chat` production routes build. |
| Browser | `corepack.cmd pnpm --filter @sejong-ai/web test:e2e` | `9 passed`; CTA keyboard navigation, no form/storage/cookie/API/third-party request, no overflow, focus, and contrast at all three viewports. |
| Secret boundary | `node scripts/check_web_bundle_secrets.mjs apps/web/.next` | Exit `0`; browser artifact exposes no prohibited server marker/value. |
| Manual browser QA | Production server at `127.0.0.1:3001` | 390/430/desktop, 200% zoom, Tab/Enter, focus, console, and Network checklist recorded in note. |
| Diff | `git diff --check` and final self-review table | No whitespace error, no data/API/DB/contract drift, no generated test artifact. |

## Security, Privacy, and Accessibility Review

- **Privacy:** There is no question field and no user-provided data. The route must not create a transcript, token, browser-storage entry, cookie, analytics event, log payload, or provider request.
- **Security:** Keep the route server-rendered and local-static. Do not expose environment values, provider credentials, API URLs, data artifact paths, or pending approval status. Q-SEC-003/A-021 still prohibits public release.
- **Data integrity:** Do not present staging, official, or mock content as an answer or source. The four labels are approved product scope, not KB records.
- **Accessibility:** Use existing semantic header/main/footer/sections; exactly one h1; skip links; native anchors; large base text; visible focus; contrast at least 4.5:1; no color-only status; and mobile/desktop/200% checks.
- **Performance/cost:** Static Server Components and local CSS require no external network or paid service. Playwright Chromium is local development tooling only and is not a shipped asset.

## Rollback

If the static flow causes a regression, revert commits in reverse order:

```powershell
git revert <docs-commit-sha>
git revert <browser-style-commit-sha>
git revert <home-cta-commit-sha>
git revert <chat-shell-commit-sha>
```

Expected result: `/chat` is removed and the home page returns to its prior truthful state with no `/chat` link. No database, API, data, migration, cache, cookie, or provider cleanup is needed because this plan creates none.

## Human Decision Boundary

Already approved by the user: Q-WEB-001=A, the static no-input `/chat` preparation route, its home CTA, and execution of this narrow WEB-HOME-001 slice. PLAN-001 already approved Playwright as test tooling; this plan fixes the exact dev-only package to `@playwright/test@1.61.1` and requires lockfile review.

Still requires a separate human decision or existing upstream completion: official-data approval materialization, DATA-SEED-001, readiness activation, API-CHAT-001, any actual chat input/API/LLM behavior, P2 behavior, public deployment, or new runtime dependency.

AI-internal choices are limited to markup structure, class names, test helpers, CSS layout mechanics, test fixtures, and documentation wording that preserves the stated claims.

## Plan Self-Review

- **Spec coverage:** Tasks 1–2 create the approved route and CTA; Task 1/2 tests preserve the exact four areas and limits; Task 3 covers no-input/no-request, responsive 390/430/desktop, keyboard/focus/contrast, no external asset, and dev dependency; Task 4 records versions, note, rollback, and handoff.
- **No placeholders:** Every code-changing task contains exact paths, commands, expected outcomes, and concrete source/test snippets. The only values filled at execution time are timestamps, measured command durations, screenshots on failure, and actual commit SHA values, which must be recorded rather than invented.
- **Type consistency:** `ChatPreparationPage`, `민원 안내 시작하기`, `준비 중인 지원 분야`, `.chat-info-grid`, and `test:e2e` use the same names across implementation and tests. The test file removes its unused helper before typecheck.
- **Scope check:** The plan intentionally excludes a form, API, data, provider, admin, official sources, and public deployment. It is a standalone, testable child slice and does not wait for the blocked data-release decisions.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-19-web-home-and-static-chat-shell.md`. Execute it with either:

1. **Subagent-Driven (recommended):** use `superpowers:subagent-driven-development`, one fresh implementation/review cycle per task.
2. **Inline Execution:** use `superpowers:executing-plans`, preserving the task boundaries and verification checkpoints above.
