import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const submitAssessment = vi.fn();
vi.mock("@/lib/api/endpoints/assessments", () => ({
  submitAssessment: (...args: unknown[]) => submitAssessment(...args),
}));

import { AssessmentRunner } from "@/features/assessments/AssessmentRunner";
import { itemsFor } from "@/features/assessments/instrument-items";
import { ApiError } from "@/lib/api/errors";
import { renderWithIntl, viMessages } from "./helpers/intl";

/** Answer the visible item by clicking its nth Likert radio (1..5). */
async function answerCurrent(
  user: ReturnType<typeof userEvent.setup>,
  likert: number,
) {
  const radios = screen.getAllByRole("radio");
  await user.click(radios[likert - 1]!);
}

describe("AssessmentRunner (FR-10/11, a11y)", () => {
  beforeEach(() => {
    submitAssessment.mockReset();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("announces progress and disables Next until the item is answered", async () => {
    const user = userEvent.setup();
    renderWithIntl(
      <AssessmentRunner instrumentType="vips" onSubmitted={vi.fn()} />,
    );

    const total = itemsFor("vips").length;
    expect(screen.getByTestId("runner-progress")).toHaveTextContent(
      `1/${total}`,
    );

    const next = screen.getByRole("button", {
      name: viMessages.assessment.next,
    });
    expect(next).toBeDisabled();

    await answerCurrent(user, 4);
    expect(next).toBeEnabled();
  });

  it("steps through every item then submits the collected answers", async () => {
    submitAssessment.mockResolvedValue({ id: "result-9" });
    const onSubmitted = vi.fn();
    const user = userEvent.setup();
    renderWithIntl(
      <AssessmentRunner instrumentType="vips" onSubmitted={onSubmitted} />,
    );

    const items = itemsFor("vips");
    for (let i = 0; i < items.length; i += 1) {
      await answerCurrent(user, 5);
      if (i < items.length - 1) {
        await user.click(
          screen.getByRole("button", { name: viMessages.assessment.next }),
        );
      }
    }

    const submit = screen.getByRole("button", {
      name: viMessages.assessment.submit,
    });
    expect(submit).toBeEnabled();
    await user.click(submit);

    await waitFor(() => expect(submitAssessment).toHaveBeenCalledTimes(1));
    const expectedAnswers = Object.fromEntries(items.map((it) => [it.key, 5]));
    expect(submitAssessment).toHaveBeenCalledWith("vips", {
      answers: expectedAnswers,
    });
    expect(onSubmitted).toHaveBeenCalledWith("result-9");
  });

  it("can go back to a previous item with Prev", async () => {
    const user = userEvent.setup();
    renderWithIntl(
      <AssessmentRunner instrumentType="riasec" onSubmitted={vi.fn()} />,
    );

    const prev = screen.getByRole("button", {
      name: viMessages.assessment.prev,
    });
    expect(prev).toBeDisabled();

    await answerCurrent(user, 3);
    await user.click(
      screen.getByRole("button", { name: viMessages.assessment.next }),
    );
    expect(screen.getByTestId("runner-progress")).toHaveTextContent("2/6");

    await user.click(prev);
    expect(screen.getByTestId("runner-progress")).toHaveTextContent("1/6");
  });

  it("surfaces a backend error message and stays on the form", async () => {
    submitAssessment.mockRejectedValue(
      new ApiError(400, "Bài làm chưa hợp lệ", "BAD_REQUEST"),
    );
    const user = userEvent.setup();
    renderWithIntl(
      <AssessmentRunner instrumentType="vips" onSubmitted={vi.fn()} />,
    );

    const items = itemsFor("vips");
    for (let i = 0; i < items.length; i += 1) {
      await answerCurrent(user, 2);
      if (i < items.length - 1) {
        await user.click(
          screen.getByRole("button", { name: viMessages.assessment.next }),
        );
      }
    }
    await user.click(
      screen.getByRole("button", { name: viMessages.assessment.submit }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Bài làm chưa hợp lệ",
    );
  });
});
