import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), prefetch: vi.fn() }),
}));

const registerAccount = vi.fn();
const resendVerification = vi.fn();
vi.mock("@/lib/api/endpoints/auth", () => ({
  register: (...args: unknown[]) => registerAccount(...args),
  resendVerification: (...args: unknown[]) => resendVerification(...args),
}));

import { RegisterForm } from "@/features/auth/RegisterForm";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore, getAccessToken } from "@/lib/auth/store";
import { renderWithIntl, viMessages } from "./helpers/intl";

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
    resendVerification.mockReset();
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

  it("on success shows the check-email notice with no session and no navigation (N-3)", async () => {
    // Register now returns 202 with no token (email-verification-2026-06.md
    // §3.1): the form is replaced by the check-email notice — it must NOT open a
    // session or route anywhere (consent routing moved to login). The child/adult
    // distinction no longer affects the register-success path, so one case covers
    // it; the <16 guardian *notice while typing* is covered by its own test above.
    registerAccount.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    await fillBaseFields(user, "1995-01-01");
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.registerSubmit }),
    );

    await waitFor(() => expect(registerAccount).toHaveBeenCalledTimes(1));
    expect(
      await screen.findByRole("heading", {
        name: viMessages.auth.checkEmailTitle,
      }),
    ).toBeInTheDocument();
    // No session, no redirect, no token in the store.
    expect(replace).not.toHaveBeenCalled();
    expect(getAccessToken()).toBeNull();
  });

  it("resends the verification email from the check-email notice", async () => {
    // From the notice, the resend button calls resendVerification(email) once and
    // surfaces the neutral (enumeration-safe) confirmation regardless of outcome.
    registerAccount.mockResolvedValue(undefined);
    resendVerification.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderWithIntl(<RegisterForm />);

    await fillBaseFields(user, "1995-01-01");
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.registerSubmit }),
    );
    await screen.findByRole("heading", {
      name: viMessages.auth.checkEmailTitle,
    });

    await user.click(
      screen.getByRole("button", { name: viMessages.auth.resend }),
    );
    await waitFor(() =>
      expect(resendVerification).toHaveBeenCalledWith("child@b.vn"),
    );
    expect(
      await screen.findByText(viMessages.auth.resendDone),
    ).toBeInTheDocument();
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
