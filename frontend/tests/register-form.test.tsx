import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), prefetch: vi.fn() }),
}));

const registerAccount = vi.fn();
const login = vi.fn();
vi.mock("@/lib/api/endpoints/auth", () => ({
  register: (...args: unknown[]) => registerAccount(...args),
  login: (...args: unknown[]) => login(...args),
}));

import { RegisterForm } from "@/features/auth/RegisterForm";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore, getAccessToken } from "@/lib/auth/store";
import { renderWithIntl, viMessages } from "./helpers/intl";

function tokenResponse(accountStatus: string, ageBand: string) {
  return {
    access_token: "registered-token",
    expires_in: 900,
    token_type: "bearer",
    user: {
      id: "u1",
      email: "child@b.vn",
      account_status: accountStatus,
      age_band: ageBand,
      user_type: "student",
      school_level: "lower_secondary",
      created_at: "2026-01-01T00:00:00Z",
    },
  };
}

async function fillBaseFields(
  user: ReturnType<typeof userEvent.setup>,
  dob: string,
) {
  await user.type(screen.getByLabelText(viMessages.auth.email), "child@b.vn");
  await user.type(screen.getByLabelText(viMessages.auth.dateOfBirth), dob);
  await user.type(screen.getByLabelText(viMessages.auth.password), "Abcdef12");
  await user.type(
    screen.getByLabelText(viMessages.auth.confirmPassword),
    "Abcdef12",
  );
}

describe("RegisterForm", () => {
  beforeEach(() => {
    replace.mockReset();
    registerAccount.mockReset();
    login.mockReset();
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("shows the guardian-consent notice when the DOB implies a child <16", async () => {
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    expect(screen.queryByText(viMessages.auth.guardianNotice)).toBeNull();
    await user.type(
      screen.getByLabelText(viMessages.auth.dateOfBirth),
      "2015-01-01",
    );
    expect(
      await screen.findByText(viMessages.auth.guardianNotice),
    ).toBeInTheDocument();
  });

  it("registers then logs in and routes a child to /consent", async () => {
    registerAccount.mockResolvedValue({ id: "u1" });
    login.mockResolvedValue(
      tokenResponse("pending_guardian_consent", "under_16"),
    );
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    await fillBaseFields(user, "2015-01-01");
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.registerSubmit }),
    );

    await waitFor(() => expect(registerAccount).toHaveBeenCalledTimes(1));
    expect(login).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(getAccessToken()).toBe("registered-token"));
    expect(replace).toHaveBeenCalledWith("/consent");
  });

  it("routes an adult registrant straight to the dashboard", async () => {
    registerAccount.mockResolvedValue({ id: "u1" });
    login.mockResolvedValue(tokenResponse("active", "adult"));
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    await fillBaseFields(user, "1995-01-01");
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.registerSubmit }),
    );

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/dashboard"));
  });

  it("surfaces the backend error message when registration fails", async () => {
    registerAccount.mockRejectedValue(
      new ApiError(409, "Email đã được sử dụng", "EMAIL_TAKEN"),
    );
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    await fillBaseFields(user, "1995-01-01");
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.registerSubmit }),
    );

    expect(
      await screen.findByText("Email đã được sử dụng"),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("falls back to the generic error for a non-API failure", async () => {
    registerAccount.mockRejectedValue(new Error("network down"));
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    await fillBaseFields(user, "1995-01-01");
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.registerSubmit }),
    );

    expect(
      await screen.findByText(viMessages.auth.genericError),
    ).toBeInTheDocument();
  });

  it("does not call the API when passwords do not match", async () => {
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    await user.type(screen.getByLabelText(viMessages.auth.email), "child@b.vn");
    await user.type(
      screen.getByLabelText(viMessages.auth.dateOfBirth),
      "1995-01-01",
    );
    await user.type(
      screen.getByLabelText(viMessages.auth.password),
      "Abcdef12",
    );
    await user.type(
      screen.getByLabelText(viMessages.auth.confirmPassword),
      "Abcdef99",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.registerSubmit }),
    );

    expect(
      await screen.findByText("Mật khẩu nhập lại không khớp"),
    ).toBeInTheDocument();
    expect(registerAccount).not.toHaveBeenCalled();
  });
});
