import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), prefetch: vi.fn() }),
}));

// The bootstrap hook performs the real network refresh; stub it so the guard's
// branching can be tested off the store status alone.
vi.mock("@/lib/auth/useSessionBootstrap", () => ({
  useSessionBootstrap: () => {},
}));

import AppLayout from "@/app/(app)/layout";
import { useAuthStore } from "@/lib/auth/store";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("(app) layout route guard", () => {
  beforeEach(() => {
    replace.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the loading state and does not redirect while bootstrapping", () => {
    useAuthStore.setState({ status: "loading", accessToken: null, user: null });

    renderWithIntl(
      <AppLayout>
        <p>Nội dung bảo vệ</p>
      </AppLayout>,
    );

    expect(screen.getByText(viMessages.common.loading)).toBeInTheDocument();
    expect(screen.queryByText("Nội dung bảo vệ")).toBeNull();
    expect(replace).not.toHaveBeenCalled();
  });

  it("redirects anonymous users to /login and hides protected children", async () => {
    useAuthStore.getState().clearSession(); // → anonymous

    renderWithIntl(
      <AppLayout>
        <p>Nội dung bảo vệ</p>
      </AppLayout>,
    );

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
    expect(screen.queryByText("Nội dung bảo vệ")).toBeNull();
  });

  it("renders children for an authenticated session", () => {
    useAuthStore.getState().setSession("jwt", {
      id: "u1",
      email: "a@b.vn",
      roles: ["working"],
    });

    renderWithIntl(
      <AppLayout>
        <p>Nội dung bảo vệ</p>
      </AppLayout>,
    );

    expect(screen.getByText("Nội dung bảo vệ")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
