import { expect, test } from "@playwright/test";

/**
 * F2 — public content slice (architecture.md §3, §11).
 *
 * These cover the anonymous, server-rendered public pages: the career library,
 * a career detail, and the public content pages. They assert the pages load
 * WITHOUT any authentication and that navigation between them works. The stack
 * is brought up by `docker-compose.test.yml` (backend + frontend) in CI; the
 * backend seed provides at least one published career + content item.
 */

test.describe("public career library (anonymous)", () => {
  test("loads the career library without logging in", async ({ page }) => {
    await page.goto("/careers");

    await expect(
      page.getByRole("heading", { level: 1, name: "Thư viện nghề nghiệp" }),
    ).toBeVisible();

    // The public/SEO contract: no auth UI is required to view this page.
    await expect(page).toHaveURL(/\/careers$/);
    // The filter form is server-rendered and usable without JS/auth.
    await expect(
      page.getByRole("form", { name: "Lọc nghề nghiệp" }),
    ).toBeVisible();
  });

  test("opens a career detail from the library and can navigate back", async ({
    page,
  }) => {
    await page.goto("/careers");

    const firstCareer = page.locator("ul li a[href^='/careers/']").first();
    await expect(firstCareer).toBeVisible();
    const name = (await firstCareer.textContent())?.trim() ?? "";

    await firstCareer.click();

    // On a detail page the career name is the H1.
    await expect(page).toHaveURL(/\/careers\/.+/);
    if (name) {
      await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
    }

    // The back link returns to the library.
    await page.getByRole("link", { name: /Về thư viện nghề/ }).click();
    await expect(page).toHaveURL(/\/careers$/);
  });

  test("filters the library via the GET form (server round-trip)", async ({
    page,
  }) => {
    await page.goto("/careers");

    await page
      .getByLabel("Trình độ đào tạo")
      .selectOption({ value: "university" });
    await page.getByRole("button", { name: "Áp dụng" }).click();

    // The filter is reflected in the URL — proving a server-side round-trip,
    // not client state.
    await expect(page).toHaveURL(/training_level=university/);
    await expect(
      page.getByRole("heading", { level: 1, name: "Thư viện nghề nghiệp" }),
    ).toBeVisible();
  });
});

test.describe("public content (anonymous)", () => {
  test("loads the public content library without logging in", async ({
    page,
  }) => {
    await page.goto("/content");

    await expect(
      page.getByRole("heading", { level: 1, name: "Nội dung hướng nghiệp" }),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/content$/);
  });

  test("opens a content item and can navigate back", async ({ page }) => {
    await page.goto("/content");

    const firstItem = page.locator("ul li a[href^='/content/']").first();
    await expect(firstItem).toBeVisible();

    await firstItem.click();
    await expect(page).toHaveURL(/\/content\/.+/);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

    await page.getByRole("link", { name: /Về danh sách nội dung/ }).click();
    await expect(page).toHaveURL(/\/content$/);
  });

  test("navigates between careers and content from the public header", async ({
    page,
  }) => {
    await page.goto("/");

    await page.getByRole("link", { name: "Thư viện nghề" }).click();
    await expect(page).toHaveURL(/\/careers$/);

    await page.getByRole("link", { name: "Nội dung hướng nghiệp" }).click();
    await expect(page).toHaveURL(/\/content$/);
  });
});
