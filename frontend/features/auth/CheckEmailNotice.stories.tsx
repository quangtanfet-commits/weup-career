import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { CheckEmailNotice } from "./CheckEmailNotice";

/**
 * Post-register "check your email" notice (email-verification-2026-06.md §3.1).
 * Presentational — the parent owns the resend call, so all three states render
 * deterministically from props (Chromatic-pinned).
 */
const meta = {
  title: "Auth/CheckEmailNotice",
  component: CheckEmailNotice,
  tags: ["autodocs"],
  parameters: { layout: "padded" },
  args: {
    email: "hocsinh@example.com",
    onResend: () => {},
  },
} satisfies Meta<typeof CheckEmailNotice>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { resendState: "idle" },
};

export const Resending: Story = {
  args: { resendState: "resending" },
};

export const ResendDone: Story = {
  args: { resendState: "done" },
};
