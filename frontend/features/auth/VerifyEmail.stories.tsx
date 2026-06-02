import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { VerifyEmailView } from "./VerifyEmailView";

/**
 * Email-verification result view (email-verification-2026-06.md §3.2). The
 * presentational layer is split from `VerifyEmailClient` so every state renders
 * without a network round-trip; the `invalid` state is identical regardless of
 * the underlying cause (no enumeration oracle).
 */
const meta = {
  title: "Auth/VerifyEmail",
  component: VerifyEmailView,
  tags: ["autodocs"],
  parameters: { layout: "padded" },
} satisfies Meta<typeof VerifyEmailView>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Verifying: Story = {
  args: { state: "verifying" },
};

export const Success: Story = {
  args: { state: "success" },
};

export const Invalid: Story = {
  args: { state: "invalid" },
};
