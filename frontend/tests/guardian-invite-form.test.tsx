import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const inviteGuardian = vi.fn();
vi.mock("@/lib/api/endpoints/guardians", () => ({
  inviteGuardian: (...args: unknown[]) => inviteGuardian(...args),
}));

import { GuardianInviteForm } from "@/features/consent/GuardianInviteForm";
import { ApiError } from "@/lib/api/errors";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("GuardianInviteForm", () => {
  beforeEach(() => {
    inviteGuardian.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("validates the guardian email before calling the API", async () => {
    const user = userEvent.setup();
    renderWithIntl(<GuardianInviteForm />);

    await user.click(
      screen.getByRole("button", { name: viMessages.consent.sendInvite }),
    );

    expect(
      await screen.findByText("Vui lòng nhập email của người giám hộ"),
    ).toBeInTheDocument();
    expect(inviteGuardian).not.toHaveBeenCalled();
  });

  it("sends the invite, shows the sent state and fires onInvited", async () => {
    inviteGuardian.mockResolvedValue({ id: "g1" });
    const onInvited = vi.fn();
    const user = userEvent.setup();
    renderWithIntl(<GuardianInviteForm onInvited={onInvited} />);

    await user.type(
      screen.getByLabelText(viMessages.consent.guardianEmail),
      "me@example.vn",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.consent.sendInvite }),
    );

    await waitFor(() => expect(inviteGuardian).toHaveBeenCalledTimes(1));
    expect(inviteGuardian).toHaveBeenCalledWith({
      guardian_email: "me@example.vn",
      relationship: "mother",
    });
    expect(
      await screen.findByText(viMessages.consent.inviteSent),
    ).toBeInTheDocument();
    expect(onInvited).toHaveBeenCalledTimes(1);
    // After a successful send the button switches to "resend".
    expect(
      screen.getByRole("button", { name: viMessages.consent.resend }),
    ).toBeInTheDocument();
  });

  it("surfaces a backend error message on failure", async () => {
    inviteGuardian.mockRejectedValue(
      new ApiError(409, "Người giám hộ đã được mời", "ALREADY_INVITED"),
    );
    const user = userEvent.setup();
    renderWithIntl(<GuardianInviteForm />);

    await user.type(
      screen.getByLabelText(viMessages.consent.guardianEmail),
      "me@example.vn",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.consent.sendInvite }),
    );

    expect(
      await screen.findByText("Người giám hộ đã được mời"),
    ).toBeInTheDocument();
  });
});
