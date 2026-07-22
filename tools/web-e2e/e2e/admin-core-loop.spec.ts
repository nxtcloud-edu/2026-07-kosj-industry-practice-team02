import { expect, test } from "@playwright/test";

test("local admin fixture keeps mock data separate from ACTIVE approval", async ({ page }) => {
  await page.goto("/admin");

  await expect(page.getByRole("heading", { name: "AI 민원 운영센터" })).toBeVisible();
  await expect(page.getByText("시연용 역할 선택 · 인증 아님")).toBeVisible();
  await expect(page.getByText("시연용 샘플 데이터")).toBeVisible();

  await page.getByRole("button", { name: /침대 프레임은 어떻게 버려요/ }).click();
  await page.getByRole("button", { name: "사유 확정" }).click();
  await page.getByRole("textbox", { name: "후보 제목" }).fill("침대 프레임 배출 안내");
  await page.getByRole("textbox", { name: "대표 질문" }).fill("침대 프레임은 어떻게 버리나요?");
  await page.getByRole("textbox", { name: "답변 요약" }).fill("시연용 샘플 안내입니다.");
  await page.getByRole("textbox", { name: "담당 부서" }).fill("자원순환 담당");
  await page.getByRole("textbox", { name: "공식 출처명" }).fill("시연용 샘플 출처");
  await page.getByRole("textbox", { name: "공식 출처 URL" }).fill("https://example.invalid/demo");
  await page.getByLabel("공식 확인일").fill("2026-07-20");
  await page.getByRole("button", { name: "KB 후보 작성" }).click();
  await page.getByRole("button", { name: "승인 요청" }).click();

  await page.getByRole("combobox", { name: "시연 역할" }).selectOption("APPROVER");
  await page.getByRole("textbox", { name: "검수 의견" }).fill("샘플 데이터 확인");
  await expect(page.getByText("시연용 샘플은 ACTIVE로 승인할 수 없습니다.")).toBeVisible();
  await expect(page.getByRole("button", { name: "승인하고 ACTIVE 반영" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "반려" })).toBeEnabled();

  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true);
  expect(await page.context().cookies()).toEqual([]);
  expect(
    await page.evaluate(() => ({
      localStorageCount: localStorage.length,
      sessionStorageCount: sessionStorage.length,
    })),
  ).toEqual({ localStorageCount: 0, sessionStorageCount: 0 });
});
