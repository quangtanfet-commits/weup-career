import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen } from "@testing-library/react";

const listSupportRequests = vi.fn();
vi.mock("@/lib/api/endpoints/wellbeing", () => ({
  listSupportRequests: (...args: unknown[]) => listSupportRequests(...args),
}));

import { SupportRequestList } from "@/features/wellbeing/SupportRequestList";
import { ApiError } from "@/lib/api/errors";
import { renderWithIntl, viMessages } from "./helpers/intl";

const base = {
  counselor_id: null,
  student_id: "u1",
  tier: "3" as const,
};

describe("SupportRequestList", () => {
  beforeEach(() => {
    listSupportRequests.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the empty state when the learner has no requests", async () => {
    listSupportRequests.mockResolvedValue([]);
    renderWithIntl(<SupportRequestList />);

    expect(
      await screen.findByText(viMessages.wellbeing.listEmpty),
    ).toBeInTheDocument();
  });

  it("renders requests with their routing status (text, not colour alone)", async () => {
    listSupportRequests.mockResolvedValue([
      {
        ...base,
        id: "sr1",
        message: "Em muốn được hỗ trợ.",
        status: "open",
        created_at: "2026-05-30T08:00:00Z",
      },
      {
        ...base,
        id: "sr2",
        message: "Cảm ơn ạ.",
        status: "acknowledged",
        created_at: "2026-05-29T08:00:00Z",
      },
    ]);
    renderWithIntl(<SupportRequestList />);

    expect(await screen.findByText("Em muốn được hỗ trợ.")).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.wellbeing.status.open),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.wellbeing.status.acknowledged),
    ).toBeInTheDocument();
  });

  it("surfaces a backend error message on failure", async () => {
    listSupportRequests.mockRejectedValue(
      new ApiError(401, "Phiên đăng nhập đã hết hạn", "UNAUTHORIZED"),
    );
    renderWithIntl(<SupportRequestList />);

    expect(
      await screen.findByText("Phiên đăng nhập đã hết hạn"),
    ).toBeInTheDocument();
  });
});
