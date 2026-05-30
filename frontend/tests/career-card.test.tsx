import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { CareerCard } from "@/features/careers/CareerCard";
import type { CareerSummary } from "@/lib/api/endpoints/careers";

const career: CareerSummary = {
  id: "c1",
  name: "Kỹ sư phần mềm",
  field: "Công nghệ thông tin",
  riasec_codes: ["R", "I"],
  training_level: "university",
  dieu5_code: "5a",
  version: 1,
};

describe("CareerCard", () => {
  it("renders the career name, field and RIASEC codes", () => {
    render(<CareerCard career={career} />);
    expect(
      screen.getByRole("heading", { name: "Kỹ sư phần mềm" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Công nghệ thông tin")).toBeInTheDocument();
    expect(screen.getByText("R")).toBeInTheDocument();
    expect(screen.getByText("I")).toBeInTheDocument();
  });
});
