import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";

import { CompetencyTree } from "@/features/progress/CompetencyTree";
import type { Competency, ProgressItem } from "@/lib/api/endpoints/progress";
import { renderWithIntl, viMessages } from "./helpers/intl";

function competency(overrides: Partial<Competency> = {}): Competency {
  return {
    area: "A_personal",
    code: "NL1",
    dieu5_codes: ["5a"],
    id: "c1",
    indicators: [
      {
        depth: "K",
        depth_label_vi: "Nhận biết",
        dieu5_code: "5a",
        id: "i-k",
        statement_vi: "Nhận biết điểm mạnh của bản thân",
      },
      {
        depth: "A",
        depth_label_vi: "Thực hiện",
        dieu5_code: "5a",
        id: "i-a",
        statement_vi: "Thực hiện đánh giá bản thân",
      },
    ],
    name_en: "Self-awareness",
    name_vi: "Tự nhận thức",
    ...overrides,
  };
}

describe("CompetencyTree (FR-20/21)", () => {
  it("renders the empty state when there are no competencies", () => {
    renderWithIntl(<CompetencyTree competencies={[]} />);
    expect(screen.getByText(viMessages.progress.empty)).toBeInTheDocument();
  });

  it("groups competencies under their ABCD area heading", () => {
    renderWithIntl(
      <CompetencyTree
        competencies={[
          competency({ id: "c1", area: "A_personal", name_vi: "Tự nhận thức" }),
          competency({
            id: "c2",
            area: "C_building",
            name_vi: "Xây dựng kế hoạch",
            indicators: [],
          }),
        ]}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: viMessages.progress.area.A_personal,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: viMessages.progress.area.C_building,
      }),
    ).toBeInTheDocument();
    // B_exploration has no competencies → no heading.
    expect(
      screen.queryByRole("heading", {
        name: viMessages.progress.area.B_exploration,
      }),
    ).toBeNull();
  });

  it("exposes indicators inside a collapsible details element", () => {
    renderWithIntl(<CompetencyTree competencies={[competency()]} />);
    // The indicator statements live inside <details> (rendered in DOM).
    expect(
      screen.getByText("Nhận biết điểm mạnh của bản thân"),
    ).toBeInTheDocument();
    expect(screen.getByText("Thực hiện đánh giá bản thân")).toBeInTheDocument();
  });

  it("marks indicators reached up to the achieved depth (prefix, CP-8)", () => {
    const progress: ProgressItem[] = [
      {
        area: "A_personal",
        code: "NL1",
        competency_id: "c1",
        depth_achieved: "K",
        depth_label_vi: "Nhận biết",
        dev_phase: "awareness",
        name_vi: "Tự nhận thức",
      },
    ];

    renderWithIntl(
      <CompetencyTree competencies={[competency()]} progress={progress} />,
    );

    // K indicator reached → "Đã đạt"; A indicator not → "Chưa đạt".
    expect(
      screen.getByText(new RegExp(`— ${viMessages.progress.achievedLabel}`)),
    ).toBeInTheDocument();
    expect(
      screen.getByText(new RegExp(`— ${viMessages.progress.notYetLabel}`)),
    ).toBeInTheDocument();
  });

  it("shows a no-indicators note for an empty competency", () => {
    renderWithIntl(
      <CompetencyTree competencies={[competency({ indicators: [] })]} />,
    );
    expect(
      screen.getByText(viMessages.progress.noIndicators),
    ).toBeInTheDocument();
  });
});
