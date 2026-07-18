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
  await expect(
    page.getByRole("region", { name: "준비 중인 지원 분야" }).getByRole("listitem"),
  ).toHaveText(allowedServices);
  await expect(page.locator("form, input, textarea, select, button")).toHaveCount(0);
  await expect(
    page.getByText("채팅 답변, 민원 신청, 개인별 조회와 공식 KB 데이터는 아직 제공하지 않습니다."),
  ).toBeVisible();

  expect(await page.context().cookies()).toEqual([]);
  expect(
    await page.evaluate(async () => ({
      indexedDbCount: (await indexedDB.databases()).length,
      localStorageCount: localStorage.length,
      sessionStorageCount: sessionStorage.length,
    })),
  ).toEqual({ indexedDbCount: 0, localStorageCount: 0, sessionStorageCount: 0 });

  const isAllowedCitizenShellRequest = (requestUrl: string) => {
    const { origin, pathname } = new URL(requestUrl);
    return (
      origin === "http://127.0.0.1:3001" &&
      (pathname === "/" || pathname === "/chat" || pathname.startsWith("/_next/static/"))
    );
  };
  expect(isAllowedCitizenShellRequest("http://127.0.0.1:3001/track")).toBe(false);
  expect(requests.every(isAllowedCitizenShellRequest)).toBe(true);
});

test("chat shell fits the viewport and retains focus and readable contrast", async ({ page }) => {
  await page.goto("/chat");

  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
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
    const parse = (value: string) =>
      value.match(/\d+/g)!.slice(0, 3).map(Number) as [number, number, number];
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
