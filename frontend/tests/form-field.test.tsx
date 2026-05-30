import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { FormField } from "@/components/composites/FormField";
import { Input } from "@/components/ui/input";

describe("FormField", () => {
  it("associates the label with the control via htmlFor/id", () => {
    render(
      <FormField id="email" label="Email">
        <Input type="email" />
      </FormField>,
    );
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("id", "email");
  });

  it("renders a hint and links it via aria-describedby", () => {
    render(
      <FormField id="pw" label="Mật khẩu" hint="Tối thiểu 8 ký tự">
        <Input type="password" />
      </FormField>,
    );
    const input = screen.getByLabelText("Mật khẩu");
    expect(input).toHaveAttribute("aria-describedby", "pw-hint");
    expect(screen.getByText("Tối thiểu 8 ký tự")).toHaveAttribute(
      "id",
      "pw-hint",
    );
  });

  it("flags the control invalid and exposes the error via role=alert", () => {
    render(
      <FormField id="email" label="Email" error="Email không hợp lệ">
        <Input type="email" />
      </FormField>,
    );
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", "email-error");
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Email không hợp lệ");
    expect(alert).toHaveAttribute("id", "email-error");
  });

  it("references both error and hint when both are present", () => {
    render(
      <FormField id="pw" label="Mật khẩu" hint="gợi ý" error="lỗi">
        <Input type="password" />
      </FormField>,
    );
    expect(screen.getByLabelText("Mật khẩu")).toHaveAttribute(
      "aria-describedby",
      "pw-error pw-hint",
    );
  });
});
