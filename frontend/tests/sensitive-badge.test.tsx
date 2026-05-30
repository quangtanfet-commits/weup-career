import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";

import { SensitiveBadge } from "@/features/assessments/SensitiveBadge";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("SensitiveBadge (CP-3, a11y: never colour alone)", () => {
  it("renders the Vietnamese label alongside a decorative lock icon", () => {
    const { container } = renderWithIntl(<SensitiveBadge />);

    // Text carries the meaning (not colour alone).
    expect(
      screen.getByText(viMessages.assessment.sensitiveBadge),
    ).toBeInTheDocument();
    expect(screen.getByTestId("sensitive-badge")).toBeInTheDocument();

    // The icon is decorative and hidden from the accessibility tree.
    const icon = container.querySelector("svg");
    expect(icon).not.toBeNull();
    expect(icon).toHaveAttribute("aria-hidden", "true");
  });
});
