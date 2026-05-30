import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders its children as a real button by default", () => {
    render(<Button>Đăng nhập</Button>);
    const btn = screen.getByRole("button", { name: "Đăng nhập" });
    expect(btn.tagName).toBe("BUTTON");
  });

  it("applies the danger variant classes", () => {
    render(<Button variant="danger">Xóa</Button>);
    expect(screen.getByRole("button", { name: "Xóa" })).toHaveClass(
      "bg-danger-600",
    );
  });

  it("renders as a child element when asChild is set (Radix Slot)", () => {
    render(
      <Button asChild>
        <a href="/nghe-nghiep">Thư viện nghề</a>
      </Button>,
    );
    const link = screen.getByRole("link", { name: "Thư viện nghề" });
    expect(link).toHaveAttribute("href", "/nghe-nghiep");
    // Slot merges the button styling onto the anchor.
    expect(link).toHaveClass("inline-flex");
  });

  it("forwards disabled state", () => {
    render(<Button disabled>Gửi</Button>);
    expect(screen.getByRole("button", { name: "Gửi" })).toBeDisabled();
  });
});
