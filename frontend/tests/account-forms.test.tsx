import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const useProfileMock = vi.fn();
const updateProfileMutate = vi.fn();
const changePasswordMutate = vi.fn();
const exportDataMutate = vi.fn();
const deleteAccountMutate = vi.fn();
const exportChildMutate = vi.fn();
const deleteChildMutate = vi.fn();

let exportDataPending = false;
let deleteAccountPending = false;
let exportChildPending = false;
let deleteChildPending = false;

vi.mock("@/features/account/useAccount", () => ({
  useProfile: () => useProfileMock(),
  useUpdateProfile: () => ({
    mutateAsync: updateProfileMutate,
    isPending: false,
  }),
  useChangePassword: () => ({
    mutateAsync: changePasswordMutate,
    isPending: false,
  }),
  useExportData: () => ({
    mutateAsync: exportDataMutate,
    isPending: exportDataPending,
  }),
  useDeleteAccount: () => ({
    mutateAsync: deleteAccountMutate,
    isPending: deleteAccountPending,
  }),
  useExportChildData: () => ({
    mutateAsync: exportChildMutate,
    isPending: exportChildPending,
  }),
  useDeleteChildAccount: () => ({
    mutateAsync: deleteChildMutate,
    isPending: deleteChildPending,
  }),
}));

import { ProfileForm } from "@/features/account/ProfileForm";
import { ChangePasswordForm } from "@/features/account/ChangePasswordForm";
import { ExportDataPanel } from "@/features/account/ExportDataPanel";
import { DeleteAccountPanel } from "@/features/account/DeleteAccountPanel";
import { ChildrenPanel } from "@/features/account/ChildrenPanel";
import { ApiError } from "@/lib/api/errors";
import { renderWithIntl, viMessages } from "./helpers/intl";

const profile = {
  id: "u1",
  email: "me@example.vn",
  age_band: "16_17" as const,
  account_status: "active" as const,
  school_level: "upper_secondary" as const,
  user_type: "student" as const,
  date_of_birth: "2009-01-01",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const deletion = {
  deleted_at: "2026-05-31T00:00:00Z",
  purge_due_at: "2026-06-30T00:00:00Z",
  recovery_window_days: 30,
  status: "deleted" as const,
};

beforeEach(() => {
  useProfileMock.mockReset();
  updateProfileMutate.mockReset();
  changePasswordMutate.mockReset();
  exportDataMutate.mockReset();
  deleteAccountMutate.mockReset();
  exportChildMutate.mockReset();
  deleteChildMutate.mockReset();
  exportDataPending = false;
  deleteAccountPending = false;
  exportChildPending = false;
  deleteChildPending = false;
});
afterEach(() => {
  vi.restoreAllMocks();
});

describe("ProfileForm", () => {
  function loaded() {
    useProfileMock.mockReturnValue({
      data: profile,
      isPending: false,
      isError: false,
      error: null,
    });
  }

  it("shows a loading status while the profile loads", () => {
    useProfileMock.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
      error: null,
    });
    renderWithIntl(<ProfileForm />);
    expect(
      screen.getByText(viMessages.account.profile.loading),
    ).toBeInTheDocument();
  });

  it("surfaces a backend error message", () => {
    useProfileMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new ApiError(401, "Phiên đã hết hạn", "UNAUTHORIZED"),
    });
    renderWithIntl(<ProfileForm />);
    expect(screen.getByText("Phiên đã hết hạn")).toBeInTheDocument();
  });

  it("falls back to a generic error for non-ApiError failures", () => {
    useProfileMock.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
      error: new Error("boom"),
    });
    renderWithIntl(<ProfileForm />);
    expect(
      screen.getByText(viMessages.account.genericError),
    ).toBeInTheDocument();
  });

  it("pre-fills and submits the editable fields, showing saved", async () => {
    loaded();
    updateProfileMutate.mockResolvedValue(profile);
    const user = userEvent.setup();
    renderWithIntl(<ProfileForm />);

    expect(screen.getByText("me@example.vn")).toBeInTheDocument();
    await user.selectOptions(
      screen.getByLabelText(viMessages.account.profile.userTypeLabel),
      "working",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.profile.submit,
      }),
    );

    await waitFor(() => expect(updateProfileMutate).toHaveBeenCalledTimes(1));
    expect(updateProfileMutate).toHaveBeenCalledWith({
      school_level: "upper_secondary",
      user_type: "working",
    });
    expect(
      await screen.findByText(viMessages.account.profile.saved),
    ).toBeInTheDocument();
  });

  it("surfaces an ApiError on a failed save", async () => {
    loaded();
    updateProfileMutate.mockRejectedValue(
      new ApiError(409, "Xung đột dữ liệu", "CONFLICT"),
    );
    const user = userEvent.setup();
    renderWithIntl(<ProfileForm />);

    await user.click(
      screen.getByRole("button", { name: viMessages.account.profile.submit }),
    );
    expect(await screen.findByText("Xung đột dữ liệu")).toBeInTheDocument();
  });

  it("falls back to a generic error when the save throws non-ApiError", async () => {
    loaded();
    updateProfileMutate.mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    renderWithIntl(<ProfileForm />);

    await user.click(
      screen.getByRole("button", { name: viMessages.account.profile.submit }),
    );
    expect(
      await screen.findByText(viMessages.account.genericError),
    ).toBeInTheDocument();
  });
});

describe("ChangePasswordForm", () => {
  it("submits the current + new password and shows success", async () => {
    changePasswordMutate.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderWithIntl(<ChangePasswordForm />);

    await user.type(
      screen.getByLabelText(viMessages.account.security.currentLabel),
      "OldPass2024",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.newLabel),
      "NewPass2024",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.confirmLabel),
      "NewPass2024",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.security.submit,
      }),
    );

    await waitFor(() => expect(changePasswordMutate).toHaveBeenCalledTimes(1));
    expect(changePasswordMutate).toHaveBeenCalledWith({
      current_password: "OldPass2024",
      new_password: "NewPass2024",
    });
    expect(
      await screen.findByText(viMessages.account.security.changed),
    ).toBeInTheDocument();
  });

  it("blocks submit and shows a mismatch error when confirmation differs", async () => {
    const user = userEvent.setup();
    renderWithIntl(<ChangePasswordForm />);

    await user.type(
      screen.getByLabelText(viMessages.account.security.currentLabel),
      "OldPass2024",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.newLabel),
      "NewPass2024",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.confirmLabel),
      "different1",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.account.security.submit }),
    );

    expect(
      await screen.findByText("Mật khẩu xác nhận chưa khớp"),
    ).toBeInTheDocument();
    expect(changePasswordMutate).not.toHaveBeenCalled();
  });

  it("surfaces an ApiError from the backend", async () => {
    changePasswordMutate.mockRejectedValue(
      new ApiError(400, "Mật khẩu hiện tại không đúng", "BAD_REQUEST"),
    );
    const user = userEvent.setup();
    renderWithIntl(<ChangePasswordForm />);

    await user.type(
      screen.getByLabelText(viMessages.account.security.currentLabel),
      "wrongpass",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.newLabel),
      "NewPass2024",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.confirmLabel),
      "NewPass2024",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.account.security.submit }),
    );

    expect(
      await screen.findByText("Mật khẩu hiện tại không đúng"),
    ).toBeInTheDocument();
  });

  it("falls back to a generic error for non-ApiError failures", async () => {
    changePasswordMutate.mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    renderWithIntl(<ChangePasswordForm />);

    await user.type(
      screen.getByLabelText(viMessages.account.security.currentLabel),
      "OldPass2024",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.newLabel),
      "NewPass2024",
    );
    await user.type(
      screen.getByLabelText(viMessages.account.security.confirmLabel),
      "NewPass2024",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.account.security.submit }),
    );

    expect(
      await screen.findByText(viMessages.account.genericError),
    ).toBeInTheDocument();
  });
});

describe("ExportDataPanel", () => {
  it("renders idle with just the export button", () => {
    renderWithIntl(<ExportDataPanel />);
    expect(
      screen.getByRole("button", {
        name: viMessages.account.data.export.submit,
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(viMessages.account.data.export.ready),
    ).not.toBeInTheDocument();
  });

  it("shows a pending label while exporting", () => {
    exportDataPending = true;
    renderWithIntl(<ExportDataPanel />);
    expect(
      screen.getByRole("button", {
        name: viMessages.account.data.export.submitting,
      }),
    ).toBeDisabled();
  });

  it("exports and renders the JSON + download link", async () => {
    exportDataMutate.mockResolvedValue({ subject_id: "u1", profile });
    const user = userEvent.setup();
    renderWithIntl(<ExportDataPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.export.submit,
      }),
    );

    expect(
      await screen.findByText(viMessages.account.data.export.ready),
    ).toBeInTheDocument();
    const link = screen.getByText(viMessages.account.data.export.download);
    expect(link.getAttribute("download")).toBe("weup-export.json");
    expect(
      screen.getByLabelText(viMessages.account.data.export.previewLabel),
    ).toHaveTextContent("subject_id");
  });

  it("surfaces an ApiError when the export fails", async () => {
    exportDataMutate.mockRejectedValue(
      new ApiError(500, "Lỗi máy chủ", "SERVER_ERROR"),
    );
    const user = userEvent.setup();
    renderWithIntl(<ExportDataPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.export.submit,
      }),
    );
    expect(await screen.findByText("Lỗi máy chủ")).toBeInTheDocument();
  });

  it("falls back to a generic error for non-ApiError failures", async () => {
    exportDataMutate.mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    renderWithIntl(<ExportDataPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.export.submit,
      }),
    );
    expect(
      await screen.findByText(viMessages.account.genericError),
    ).toBeInTheDocument();
  });
});

describe("DeleteAccountPanel", () => {
  it("requires an explicit confirm step before deleting", async () => {
    deleteAccountMutate.mockResolvedValue(deletion);
    const user = userEvent.setup();
    renderWithIntl(<DeleteAccountPanel />);

    // First click only reveals the confirm prompt — no call yet.
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.start,
      }),
    );
    expect(deleteAccountMutate).not.toHaveBeenCalled();
    expect(
      screen.getByText(viMessages.account.data.delete.confirmPrompt),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.confirm,
      }),
    );
    await waitFor(() => expect(deleteAccountMutate).toHaveBeenCalledTimes(1));
    expect(
      await screen.findByText(viMessages.account.data.delete.done),
    ).toBeInTheDocument();
    // Recovery window is surfaced explicitly (days + purge date).
    expect(screen.getByText(/30 ngày/)).toBeInTheDocument();
  });

  it("can cancel the confirm step", async () => {
    const user = userEvent.setup();
    renderWithIntl(<DeleteAccountPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.start,
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.cancel,
      }),
    );
    expect(
      screen.queryByText(viMessages.account.data.delete.confirmPrompt),
    ).not.toBeInTheDocument();
    expect(deleteAccountMutate).not.toHaveBeenCalled();
  });

  it("surfaces an ApiError when deletion fails", async () => {
    deleteAccountMutate.mockRejectedValue(
      new ApiError(403, "Không có quyền", "FORBIDDEN"),
    );
    const user = userEvent.setup();
    renderWithIntl(<DeleteAccountPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.start,
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.confirm,
      }),
    );
    expect(await screen.findByText("Không có quyền")).toBeInTheDocument();
  });

  it("falls back to a generic error for non-ApiError failures", async () => {
    deleteAccountMutate.mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    renderWithIntl(<DeleteAccountPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.start,
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.data.delete.confirm,
      }),
    );
    expect(
      await screen.findByText(viMessages.account.genericError),
    ).toBeInTheDocument();
  });
});

describe("ChildrenPanel (guardian)", () => {
  it("validates a non-empty child id before exporting", async () => {
    const user = userEvent.setup();
    renderWithIntl(<ChildrenPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.export.submit,
      }),
    );
    expect(
      await screen.findByText("Hãy nhập mã định danh của trẻ"),
    ).toBeInTheDocument();
    expect(exportChildMutate).not.toHaveBeenCalled();
  });

  it("exports a child's data once an id is entered", async () => {
    exportChildMutate.mockResolvedValue({ subject_id: "c1" });
    const user = userEvent.setup();
    renderWithIntl(<ChildrenPanel />);

    await user.type(
      screen.getByLabelText(viMessages.account.children.childIdLabel),
      "c1",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.export.submit,
      }),
    );

    await waitFor(() => expect(exportChildMutate).toHaveBeenCalledWith("c1"));
    expect(
      await screen.findByText(viMessages.account.children.export.ready),
    ).toBeInTheDocument();
  });

  it("surfaces an ApiError when the child export fails", async () => {
    exportChildMutate.mockRejectedValue(
      new ApiError(404, "Không tìm thấy trẻ", "NOT_FOUND"),
    );
    const user = userEvent.setup();
    renderWithIntl(<ChildrenPanel />);

    await user.type(
      screen.getByLabelText(viMessages.account.children.childIdLabel),
      "c1",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.export.submit,
      }),
    );
    expect(await screen.findByText("Không tìm thấy trẻ")).toBeInTheDocument();
  });

  it("requires confirm then soft-deletes a child with recovery window", async () => {
    deleteChildMutate.mockResolvedValue(deletion);
    const user = userEvent.setup();
    renderWithIntl(<ChildrenPanel />);

    await user.type(
      screen.getByLabelText(viMessages.account.children.childIdLabel),
      "c1",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.delete.start,
      }),
    );
    expect(deleteChildMutate).not.toHaveBeenCalled();
    expect(
      screen.getByText(viMessages.account.children.delete.confirmPrompt),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.delete.confirm,
      }),
    );
    await waitFor(() => expect(deleteChildMutate).toHaveBeenCalledWith("c1"));
    expect(
      await screen.findByText(viMessages.account.children.delete.done),
    ).toBeInTheDocument();
    expect(screen.getByText(/30 ngày/)).toBeInTheDocument();
  });

  it("does not open the confirm step when the child id is empty", async () => {
    const user = userEvent.setup();
    renderWithIntl(<ChildrenPanel />);

    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.delete.start,
      }),
    );
    expect(
      screen.queryByText(viMessages.account.children.delete.confirmPrompt),
    ).not.toBeInTheDocument();
    expect(
      await screen.findByText("Hãy nhập mã định danh của trẻ"),
    ).toBeInTheDocument();
  });

  it("can cancel the child delete confirm step", async () => {
    const user = userEvent.setup();
    renderWithIntl(<ChildrenPanel />);

    await user.type(
      screen.getByLabelText(viMessages.account.children.childIdLabel),
      "c1",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.delete.start,
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.delete.cancel,
      }),
    );
    expect(
      screen.queryByText(viMessages.account.children.delete.confirmPrompt),
    ).not.toBeInTheDocument();
    expect(deleteChildMutate).not.toHaveBeenCalled();
  });

  it("falls back to a generic error when child deletion throws non-ApiError", async () => {
    deleteChildMutate.mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    renderWithIntl(<ChildrenPanel />);

    await user.type(
      screen.getByLabelText(viMessages.account.children.childIdLabel),
      "c1",
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.delete.start,
      }),
    );
    await user.click(
      screen.getByRole("button", {
        name: viMessages.account.children.delete.confirm,
      }),
    );
    expect(
      await screen.findByText(viMessages.account.genericError),
    ).toBeInTheDocument();
  });
});
