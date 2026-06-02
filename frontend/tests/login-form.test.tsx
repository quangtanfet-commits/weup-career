import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), prefetch: vi.fn() }),
}));

const login = vi.fn();
const resendVerification = vi.fn();
vi.mock("@/lib/api/endpoints/auth", () => ({
  login: (...args: unknown[]) => login(...args),
  resendVerification: (...args: unknown[]) => resendVerification(...args),
}));

import { LoginForm } from "@/features/auth/LoginForm";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore, getAccessToken } from "@/lib/auth/store";
import { renderWithIntl, viMessages } from "./helpers/intl";

const tokenResponse = {
  access_token: "logged-in-token",
  expires_in: 900,
  token_type: "bearer",
  user: {
    id: "u1",
    email: "a@b.vn",
    account_status: "active",
    age_band: "adult",
    user_type: "working",
    school_level: "tertiary",
    created_at: "2026-01-01T00:00:00Z",
  },
};

describe("LoginForm", () => {
  beforeEach(() => {
    replace.mockReset();
    login.mockReset();
    resendVerification.mockReset();
    useAuthStore.getState().clearSession();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    useAuthStore.getState().clearSession();
  });

  it("shows validation errors and does not call the API on empty submit", async () => {
    const user = userEvent.setup();
    renderWithIntl(<LoginForm />);

    await user.click(
      screen.getByRole("button", { name: viMessages.auth.loginSubmit }),
    );

    expect(await screen.findByText("Vui lòng nhập email")).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
  });

  it("logs in, stores the in-memory token and redirects on success", async () => {
    login.mockResolvedValue(tokenResponse);
    const user = userEvent.setup();
    renderWithIntl(<LoginForm />);

    await user.type(screen.getByLabelText(viMessages.auth.email), "a@b.vn");
    await user.type(
      screen.getByLabelText(viMessages.auth.password),
      "abcdef12",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.loginSubmit }),
    );

    await waitFor(() => expect(login).toHaveBeenCalledTimes(1));
    expect(login).toHaveBeenCalledWith({
      email: "a@b.vn",
      password: "abcdef12",
    });
    await waitFor(() => expect(getAccessToken()).toBe("logged-in-token"));
    expect(replace).toHaveBeenCalledWith("/dashboard");
  });

  it("redirects to a custom target when redirectTo is provided", async () => {
    login.mockResolvedValue(tokenResponse);
    const user = userEvent.setup();
    renderWithIntl(<LoginForm redirectTo="/consent" />);

    await user.type(screen.getByLabelText(viMessages.auth.email), "a@b.vn");
    await user.type(
      screen.getByLabelText(viMessages.auth.password),
      "abcdef12",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.loginSubmit }),
    );

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/consent"));
  });

  it("surfaces the backend error message on a failed login", async () => {
    login.mockRejectedValue(
      new ApiError(
        401,
        "Email hoặc mật khẩu không đúng",
        "INVALID_CREDENTIALS",
      ),
    );
    const user = userEvent.setup();
    renderWithIntl(<LoginForm />);

    await user.type(screen.getByLabelText(viMessages.auth.email), "a@b.vn");
    await user.type(
      screen.getByLabelText(viMessages.auth.password),
      "abcdef12",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.loginSubmit }),
    );

    expect(
      await screen.findByText("Email hoặc mật khẩu không đúng"),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("falls back to the generic error for a non-API failure", async () => {
    login.mockRejectedValue(new Error("network down"));
    const user = userEvent.setup();
    renderWithIntl(<LoginForm />);

    await user.type(screen.getByLabelText(viMessages.auth.email), "a@b.vn");
    await user.type(
      screen.getByLabelText(viMessages.auth.password),
      "abcdef12",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.loginSubmit }),
    );

    expect(
      await screen.findByText(viMessages.auth.genericError),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("routes a verified pending-consent session to /consent (N-3)", async () => {
    login.mockResolvedValue({
      ...tokenResponse,
      user: {
        ...tokenResponse.user,
        account_status: "pending_guardian_consent",
      },
    });
    const user = userEvent.setup();
    renderWithIntl(<LoginForm />);

    await user.type(screen.getByLabelText(viMessages.auth.email), "a@b.vn");
    await user.type(
      screen.getByLabelText(viMessages.auth.password),
      "abcdef12",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.loginSubmit }),
    );

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/consent"));
  });

  it("on 403 EMAIL_NOT_VERIFIED shows the not-verified notice and resends (N-3)", async () => {
    // A correct password on an unverified account returns 403 — a distinct
    // message (not the generic 401) with a resend affordance, and no navigation.
    login.mockRejectedValue(new ApiError(403, "unused", "EMAIL_NOT_VERIFIED"));
    resendVerification.mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderWithIntl(<LoginForm />);

    await user.type(screen.getByLabelText(viMessages.auth.email), "a@b.vn");
    await user.type(
      screen.getByLabelText(viMessages.auth.password),
      "abcdef12",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.loginSubmit }),
    );

    expect(
      await screen.findByText(viMessages.auth.emailNotVerified),
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();

    // The resend affordance resends to the entered email and confirms neutrally.
    await user.click(
      screen.getByRole("button", { name: viMessages.auth.resend }),
    );
    await waitFor(() =>
      expect(resendVerification).toHaveBeenCalledWith("a@b.vn"),
    );
    expect(
      await screen.findByText(viMessages.auth.resendDone),
    ).toBeInTheDocument();
  });
});
