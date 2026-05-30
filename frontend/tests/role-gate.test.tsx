import { describe, it, expect, afterEach } from "vitest";
import { act, screen } from "@testing-library/react";

import { RoleGate } from "@/components/composites/RoleGate";
import { useAuthStore } from "@/lib/auth/store";
import { renderWithIntl, viMessages } from "./helpers/intl";

/**
 * RoleGate (architecture.md §5.3, §7; CP-4). The reusable client role guard:
 * loading → shared loading copy; authenticated-without-role → neutral no-access
 * block (no info leak, no redirect); has-role → children.
 */
describe("RoleGate", () => {
  afterEach(() => {
    act(() => useAuthStore.getState().clearSession());
  });

  it("shows the loading state while the session is bootstrapping", () => {
    act(() => useAuthStore.setState({ status: "loading", user: null }));

    renderWithIntl(
      <RoleGate roles={["counselor"]}>
        <p>Bảng điều khiển</p>
      </RoleGate>,
    );

    expect(screen.getByText(viMessages.common.loading)).toBeInTheDocument();
    expect(screen.queryByText("Bảng điều khiển")).toBeNull();
  });

  it("blocks an authenticated user who lacks the required role (neutral, no leak)", () => {
    act(() =>
      useAuthStore.getState().setSession("jwt", {
        id: "u1",
        email: "adult@example.vn",
        roles: ["working"],
      }),
    );

    renderWithIntl(
      <RoleGate roles={["counselor"]}>
        <p>Bảng điều khiển</p>
      </RoleGate>,
    );

    expect(
      screen.getByText(viMessages.common.noAccessTitle),
    ).toBeInTheDocument();
    // The protected content is never rendered for a non-counselor.
    expect(screen.queryByText("Bảng điều khiển")).toBeNull();
  });

  it("renders children when the user holds a required role", () => {
    act(() =>
      useAuthStore.getState().setSession("jwt", {
        id: "c1",
        email: "counselor@example.vn",
        roles: ["counselor"],
      }),
    );

    renderWithIntl(
      <RoleGate roles={["counselor"]}>
        <p>Bảng điều khiển</p>
      </RoleGate>,
    );

    expect(screen.getByText("Bảng điều khiển")).toBeInTheDocument();
    expect(screen.queryByText(viMessages.common.noAccessTitle)).toBeNull();
  });
});
