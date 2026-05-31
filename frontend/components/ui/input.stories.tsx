import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Input } from "./input";

/**
 * Input primitive — the text-field surface used across the F1 auth forms. Covers
 * the four visual states the design tokens distinguish: default, placeholder,
 * disabled, and `aria-invalid` (the red `--danger-600` border the Zod error path
 * sets). Chromatic pins each so a token regression is caught.
 */
const meta = {
  title: "UI/Input",
  component: Input,
  tags: ["autodocs"],
  parameters: { layout: "padded" },
  args: { placeholder: "you@example.com" },
  argTypes: {
    disabled: { control: "boolean" },
    type: {
      control: "select",
      options: ["text", "email", "password", "date"],
    },
  },
} satisfies Meta<typeof Input>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { defaultValue: "an@weup.vn" } };
export const Placeholder: Story = {};
export const Disabled: Story = {
  args: { disabled: true, defaultValue: "an@weup.vn" },
};

/** The error state — `aria-invalid` flips the border to `--danger-600`. */
export const Invalid: Story = {
  args: { "aria-invalid": true, defaultValue: "không-hợp-lệ" },
};

export const Password: Story = {
  args: { type: "password", defaultValue: "WeUpPass123" },
};

/** All states side by side — the canonical Chromatic snapshot. */
export const AllStates: Story = {
  render: () => (
    <div className="flex max-w-sm flex-col gap-3">
      <Input defaultValue="an@weup.vn" />
      <Input placeholder="you@example.com" />
      <Input disabled defaultValue="an@weup.vn" />
      <Input aria-invalid defaultValue="không-hợp-lệ" />
    </div>
  ),
};
