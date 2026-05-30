import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";

import { DeSensitizedStudentView } from "@/features/counseling/DeSensitizedStudentView";
import type { StudentProgressOut } from "@/lib/api/endpoints/counseling";
import { renderWithIntl, viMessages } from "./helpers/intl";

/**
 * DeSensitizedStudentView (architecture.md §4.4; FR-82, CP-3). Asserts the view
 * surfaces ONLY de-sensitized data — competency progress + assessment summary
 * codes — and makes the de-sensitization explicit, never a raw payload.
 */
const data: StudentProgressOut = {
  student_id: "stu-1",
  progress: [
    {
      area: "A_personal",
      code: "NL1",
      competency_id: "c1",
      depth_achieved: "A",
      dev_phase: "exploration",
      name_vi: "Tự nhận thức",
    },
  ],
  assessments: [
    { instrument_type: "RIASEC", summary_code: "RIA" },
    { instrument_type: "MBTI", summary_code: null },
  ],
};

describe("DeSensitizedStudentView", () => {
  it("shows the de-sensitized banner, progress and assessment summary codes", () => {
    renderWithIntl(<DeSensitizedStudentView data={data} />);

    // CP-3 banner makes the de-sensitization explicit to the counselor.
    expect(
      screen.getByText(viMessages.counselor.desensitizedNote),
    ).toBeInTheDocument();

    // De-sensitized competency progress (name + derived depth/phase labels).
    expect(screen.getByText("Tự nhận thức")).toBeInTheDocument();

    // Assessments show instrument + derived summary code only.
    expect(screen.getByText("RIASEC")).toBeInTheDocument();
    expect(screen.getByText("RIA")).toBeInTheDocument();
    // A missing summary code degrades to a neutral label, not a raw payload.
    expect(
      screen.getByText(viMessages.counselor.noSummaryCode),
    ).toBeInTheDocument();
  });

  it("shows neutral empty states when the student has no data", () => {
    renderWithIntl(
      <DeSensitizedStudentView
        data={{ student_id: "stu-2", progress: [], assessments: [] }}
      />,
    );

    expect(
      screen.getByText(viMessages.counselor.studentProgressEmpty),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.counselor.assessmentsEmpty),
    ).toBeInTheDocument();
  });
});
