import { describe, it, expect, vi, afterEach } from "vitest";
import { screen } from "@testing-library/react";

const useSupportRequestsMock = vi.fn();
vi.mock("@/features/wellbeing/useWellbeing", () => ({
  useSupportRequests: () => useSupportRequestsMock(),
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
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the loading state while the query is pending", () => {
    useSupportRequestsMock.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      error: null,
    });
    renderWithIntl(<SupportRequestList />);

    expect(
      screen.getByText(viMessages.wellbeing.listLoading),
    ).toBeInTheDocument();
  });

  it("shows the empty state when the learner has no requests", () => {
    useSupportRequestsMock.mockReturnValue({
      data: [],
      isPending: false,
      isError: false,
      error: null,
    });
    renderWithIntl(<SupportRequestList />);

    expect(
      screen.getByText(viMessages.wellbeing.listEmpty),
    ).toBeInTheDocument();
  });

  it("renders requests with their routing status (text, not colour alone)", () => {
    useSupportRequestsMock.mockReturnValue({
      data: [
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
      ],
      isPending: false,
      isError: false,
      error: null,
    });
    renderWithIntl(<SupportRequestList />);

    expect(screen.getByText("Em muốn được hỗ trợ.")).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.wellbeing.status.open),
    ).toBeInTheDocument();
    expect(
      screen.getByText(viMessages.wellbeing.status.acknowledged),
    ).toBeInTheDocument();
  });

  it("surfaces a backend error message on failure", () => {
    useSupportRequestsMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new ApiError(401, "Phiên đăng nhập đã hết hạn", "UNAUTHORIZED"),
    });
    renderWithIntl(<SupportRequestList />);

    expect(screen.getByText("Phiên đăng nhập đã hết hạn")).toBeInTheDocument();
  });
});
