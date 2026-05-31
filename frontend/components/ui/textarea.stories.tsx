import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Textarea } from "./textarea";

/**
 * Textarea primitive — the multi-line free-text field (e.g. the F6 wellbeing
 * support-request message). Mirrors `Input` styling with a `min-h-24` floor.
 * Covers default, placeholder, disabled, and the `aria-invalid` error border.
 */
const meta = {
  title: "UI/Textarea",
  component: Textarea,
  tags: ["autodocs"],
  parameters: { layout: "padded" },
  args: { placeholder: "Mô tả điều bạn đang gặp phải…" },
  argTypes: { disabled: { control: "boolean" } },
  render: (args) => <Textarea {...args} className="max-w-md" />,
} satisfies Meta<typeof Textarea>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { defaultValue: "Gần đây mình thấy khá áp lực việc chọn ngành." },
};
export const Placeholder: Story = {};
export const Disabled: Story = {
  args: {
    disabled: true,
    defaultValue: "Trường đã tiếp nhận yêu cầu của bạn.",
  },
};

/** The error state — `aria-invalid` flips the border to `--danger-600`. */
export const Invalid: Story = { args: { "aria-invalid": true } };
