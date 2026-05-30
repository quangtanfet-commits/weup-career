import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";

import { DepthStepper } from "@/features/progress/DepthStepper";
import { renderWithIntl, viMessages } from "./helpers/intl";

const labels = viMessages.progress.depth;

describe("DepthStepper (CP-8)", () => {
  it("renders all three K→A→R rungs with Vietnamese labels", () => {
    renderWithIntl(<DepthStepper achieved="A" />);
    expect(screen.getByText(labels.K)).toBeInTheDocument();
    expect(screen.getByText(labels.A)).toBeInTheDocument();
    expect(screen.getByText(labels.R)).toBeInTheDocument();
  });

  it("marks reached rungs as achieved and the rest as not-yet (text, not colour only)", () => {
    renderWithIntl(<DepthStepper achieved="A" />);
    const list = screen.getByRole("list");
    const items = within(list).getAllByRole("listitem");
    expect(items).toHaveLength(3);

    // K and A reached → "Đã đạt"; R not → "Chưa đạt".
    expect(
      within(items[0]!).getByText(`(${viMessages.progress.achievedLabel})`),
    ).toBeInTheDocument();
    expect(
      within(items[1]!).getByText(`(${viMessages.progress.achievedLabel})`),
    ).toBeInTheDocument();
    expect(
      within(items[2]!).getByText(`(${viMessages.progress.notYetLabel})`),
    ).toBeInTheDocument();
  });

  it("marks nothing reached when there is no progress yet", () => {
    renderWithIntl(<DepthStepper achieved={null} />);
    const notYet = screen.getAllByText(`(${viMessages.progress.notYetLabel})`);
    expect(notYet).toHaveLength(3);
  });

  it("renders no interactive control (read-only: no downgrade UI)", () => {
    renderWithIntl(<DepthStepper achieved="R" />);
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.queryByRole("slider")).toBeNull();
  });
});
