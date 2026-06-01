import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const createMutate = vi.fn();
vi.mock("@/features/wellbeing/useWellbeing", () => ({
  useCreateSupportRequest: () => ({
    mutateAsync: createMutate,
    isPending: false,
  }),
}));

import { SupportRequestForm } from "@/features/wellbeing/SupportRequestForm";
import { ApiError } from "@/lib/api/errors";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("SupportRequestForm", () => {
  beforeEach(() => {
    createMutate.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("validates a non-empty message before calling the mutation", async () => {
    const user = userEvent.setup();
    renderWithIntl(<SupportRequestForm />);

    await user.click(
      screen.getByRole("button", { name: viMessages.wellbeing.submit }),
    );

    expect(
      await screen.findByText(
        "Hãy chia sẻ đôi điều để chúng tôi kết nối bạn với người hỗ trợ",
      ),
    ).toBeInTheDocument();
    expect(createMutate).not.toHaveBeenCalled();
  });

  it("submits the request and shows the sent state", async () => {
    createMutate.mockResolvedValue({ id: "sr1" });
    const user = userEvent.setup();
    renderWithIntl(<SupportRequestForm />);

    await user.type(
      screen.getByLabelText(viMessages.wellbeing.messageLabel),
      "Dạo này em thấy hơi mệt và muốn nói chuyện với ai đó.",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.wellbeing.submit }),
    );

    await waitFor(() => expect(createMutate).toHaveBeenCalledTimes(1));
    expect(createMutate).toHaveBeenCalledWith({
      message: "Dạo này em thấy hơi mệt và muốn nói chuyện với ai đó.",
    });
    expect(
      await screen.findByText(viMessages.wellbeing.requestSent),
    ).toBeInTheDocument();
    // After a successful send the button switches to "send another".
    expect(
      screen.getByRole("button", { name: viMessages.wellbeing.sendAnother }),
    ).toBeInTheDocument();
  });

  it("surfaces a backend error message on failure", async () => {
    createMutate.mockRejectedValue(
      new ApiError(403, "Cần có sự đồng ý của người giám hộ", "CONSENT"),
    );
    const user = userEvent.setup();
    renderWithIntl(<SupportRequestForm />);

    await user.type(
      screen.getByLabelText(viMessages.wellbeing.messageLabel),
      "Em muốn được hỗ trợ.",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.wellbeing.submit }),
    );

    expect(
      await screen.findByText("Cần có sự đồng ý của người giám hộ"),
    ).toBeInTheDocument();
  });
});
