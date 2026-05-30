import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

describe("Card", () => {
  it("composes header, title, description and content", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Kỹ sư phần mềm</CardTitle>
          <CardDescription>Công nghệ thông tin</CardDescription>
        </CardHeader>
        <CardContent>Nội dung</CardContent>
      </Card>,
    );

    expect(
      screen.getByRole("heading", { name: "Kỹ sư phần mềm" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Công nghệ thông tin")).toBeInTheDocument();
    expect(screen.getByText("Nội dung")).toBeInTheDocument();
  });

  it("merges custom class names onto the surface", () => {
    render(<Card className="custom-card">x</Card>);
    expect(screen.getByText("x")).toHaveClass("custom-card", "shadow-sm");
  });

  it("renders a footer region", () => {
    render(
      <Card>
        <CardFooter>
          <span>Hành động</span>
        </CardFooter>
      </Card>,
    );
    expect(screen.getByText("Hành động")).toBeInTheDocument();
  });
});
