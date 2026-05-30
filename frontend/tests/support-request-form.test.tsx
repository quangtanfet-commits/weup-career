import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const createSupportRequest = vi.fn();
vi.mock("@/lib/api/endpoints/wellbeing", () => ({
  createSupportRequest: (...args: unknown[]) => createSupportRequest(...args),
}));

import { SupportRequestForm } from "@/features/wellbeing/SupportRequestForm";
import { ApiError } from "@/lib/api/errors";
import { renderWithIntl, viMessages } from "./helpers/intl";

describe("SupportRequestForm", () => {
  beforeEach(() => {
    createSupportRequest.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("validates a non-empty message before calling the API", async () => {
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
    expect(createSupportRequest).not.toHaveBeenCalled();
  });

  it("submits the request, shows the sent state and fires onCreated", async () => {
    createSupportRequest.mockResolvedValue({ id: "sr1" });
    const onCreated = vi.fn();
    const user = userEvent.setup();
    renderWithIntl(<SupportRequestForm onCreated={onCreated} />);

    await user.type(
      screen.getByLabelText(viMessages.wellbeing.messageLabel),
      "Dạo này em thấy hơi mệt và muốn nói chuyện với ai đó.",
    );
    await user.click(
      screen.getByRole("button", { name: viMessages.wellbeing.submit }),
    );

    await waitFor(() => expect(createSupportRequest).toHaveBeenCalledTimes(1));
    expect(createSupportRequest).toHaveBeenCalledWith({
      message: "Dạo này em thấy hơi mệt và muốn nói chuyện với ai đó.",
    });
    expect(
      await screen.findByText(viMessages.wellbeing.requestSent),
    ).toBeInTheDocument();
    expect(onCreated).toHaveBeenCalledTimes(1);
    // After a successful send the button switches to "send another".
    expect(
      screen.getByRole("button", { name: viMessages.wellbeing.sendAnother }),
    ).toBeInTheDocument();
  });

  it("surfaces a backend error message on failure", async () => {
    createSupportRequest.mockRejectedValue(
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
