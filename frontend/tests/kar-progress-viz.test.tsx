import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";

import { KARProgressViz } from "@/features/progress/KARProgressViz";
import type { ProgressItem } from "@/lib/api/endpoints/progress";
import { renderWithIntl, viMessages } from "./helpers/intl";

function item(overrides: Partial<ProgressItem> = {}): ProgressItem {
  return {
    area: "A_personal",
    code: "NL1",
    competency_id: "c1",
    depth_achieved: "A",
    depth_label_vi: "Thực hiện",
    dev_phase: "exploration",
    name_vi: "Tự nhận thức",
    ...overrides,
  };
}

describe("KARProgressViz", () => {
  it("renders the empty state when there is no progress", () => {
    renderWithIntl(<KARProgressViz items={[]} />);
    expect(screen.getByText(viMessages.progress.empty)).toBeInTheDocument();
  });

  it("lists each competency with its current depth label", () => {
    renderWithIntl(
      <KARProgressViz
        items={[
          item({ competency_id: "c1", name_vi: "Tự nhận thức" }),
          item({
            competency_id: "c2",
            name_vi: "Khám phá nghề",
            depth_achieved: null,
            depth_label_vi: null,
          }),
        ]}
      />,
    );

    expect(screen.getByText("Tự nhận thức")).toBeInTheDocument();
    expect(screen.getByText("Khám phá nghề")).toBeInTheDocument();
    // The no-progress competency shows the "not started" fallback label.
    expect(
      screen.getByText(new RegExp(viMessages.progress.noProgressYet)),
    ).toBeInTheDocument();
  });

  it("orders the most-advanced competency first", () => {
    renderWithIntl(
      <KARProgressViz
        items={[
          item({
            competency_id: "c1",
            code: "NL1",
            name_vi: "Mức K",
            depth_achieved: "K",
          }),
          item({
            competency_id: "c2",
            code: "NL2",
            name_vi: "Mức R",
            depth_achieved: "R",
          }),
        ]}
      />,
    );

    // The DepthStepper inside each row is its own list; scope to the outer
    // competency list (the one whose direct items carry the competency names).
    const outerList = screen.getAllByRole("list").find((list) =>
      within(list)
        .queryAllByRole("listitem")
        .some((li) => (li.textContent ?? "").includes("Mức R")),
    )!;
    const rows = within(outerList)
      .getAllByRole("listitem")
      .filter((li) => /Mức [KR]/.test(li.textContent ?? ""));
    const names = rows.map((li) => li.textContent ?? "");
    const idxR = names.findIndex((n) => n.includes("Mức R"));
    const idxK = names.findIndex((n) => n.includes("Mức K"));
    expect(idxR).toBeGreaterThanOrEqual(0);
    expect(idxR).toBeLessThan(idxK);
  });
});
