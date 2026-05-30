import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";

import { DevPhasePanel } from "@/features/progress/DevPhasePanel";
import type { ProgressItem } from "@/lib/api/endpoints/progress";
import { renderWithIntl, viMessages } from "./helpers/intl";

function item(overrides: Partial<ProgressItem> = {}): ProgressItem {
  return {
    area: "A_personal",
    code: "NL1",
    competency_id: "c1",
    depth_achieved: "K",
    depth_label_vi: "Nhận biết",
    dev_phase: "awareness",
    name_vi: "Tự nhận thức",
    ...overrides,
  };
}

describe("DevPhasePanel (FR-23)", () => {
  it("renders the empty state with no progress rows", () => {
    renderWithIntl(<DevPhasePanel items={[]} />);
    expect(screen.getByText(viMessages.progress.empty)).toBeInTheDocument();
  });

  it("shows one phase per area (non-linear ABCD: different phases coexist)", () => {
    renderWithIntl(
      <DevPhasePanel
        items={[
          item({
            competency_id: "c1",
            area: "A_personal",
            dev_phase: "awareness",
          }),
          item({
            competency_id: "c2",
            area: "A_personal",
            dev_phase: "awareness",
          }),
          item({
            competency_id: "c3",
            area: "C_building",
            dev_phase: "planning",
          }),
        ]}
      />,
    );

    // A_personal heading once (collapsed to a single area row), C_building once.
    expect(
      screen.getByText(viMessages.progress.area.A_personal),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.progress.area.C_building),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.progress.devPhase.awareness),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.progress.devPhase.planning),
    ).toBeInTheDocument();
  });

  it("renders areas in canonical A→B→C order", () => {
    renderWithIntl(
      <DevPhasePanel
        items={[
          item({
            competency_id: "c1",
            area: "C_building",
            dev_phase: "planning",
          }),
          item({
            competency_id: "c2",
            area: "A_personal",
            dev_phase: "awareness",
          }),
        ]}
      />,
    );

    const terms = screen.getAllByRole("term").map((t) => t.textContent ?? "");
    const idxA = terms.indexOf(viMessages.progress.area.A_personal);
    const idxC = terms.indexOf(viMessages.progress.area.C_building);
    expect(idxA).toBeGreaterThanOrEqual(0);
    expect(idxA).toBeLessThan(idxC);
  });
});
