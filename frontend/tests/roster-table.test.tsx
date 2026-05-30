import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";

import { RosterTable } from "@/features/counseling/RosterTable";
import type { RosterEntryOut } from "@/lib/api/endpoints/counseling";
import { renderWithIntl, viMessages } from "./helpers/intl";

/**
 * RosterTable (architecture.md §4.4; FR-82, CP-3). Renders the de-sensitized
 * roster rows (email + class) with a link to each student's view.
 */
const entries: RosterEntryOut[] = [
  { user_id: "u1", email: "hs1@example.vn", class_id: "10A1" },
  { user_id: "u2", email: "hs2@example.vn", class_id: null },
];

describe("RosterTable", () => {
  it("renders one row per de-sensitized roster entry with a view link", () => {
    renderWithIntl(<RosterTable entries={entries} />);

    expect(screen.getByText("hs1@example.vn")).toBeInTheDocument();
    expect(screen.getByText("10A1")).toBeInTheDocument();
    // A null class degrades to a neutral label.
    expect(
      screen.getByText(viMessages.counselor.rosterNoClass),
    ).toBeInTheDocument();

    const links = screen.getAllByRole("link", {
      name: viMessages.counselor.rosterView,
    });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "/counselor/students/u1");
  });
});
