import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Select } from "./select";

/**
 * Native `<select>` styled to the design tokens — the enum control used in F1
 * (school_level, user_type). Native rather than a Radix listbox so it is
 * keyboard- and screen-reader-accessible out of the box (architecture.md §8).
 * Covers default, disabled, and the `aria-invalid` error border.
 */
const meta = {
  title: "UI/Select",
  component: Select,
  tags: ["autodocs"],
  parameters: { layout: "padded" },
  argTypes: { disabled: { control: "boolean" } },
  render: (args) => (
    <Select {...args} className="max-w-xs">
      <option value="">Chọn cấp học</option>
      <option value="thcs">THCS</option>
      <option value="thpt">THPT</option>
      <option value="working">Đang đi làm</option>
    </Select>
  ),
} satisfies Meta<typeof Select>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Selected: Story = { args: { defaultValue: "thpt" } };
export const Disabled: Story = {
  args: { disabled: true, defaultValue: "thcs" },
};

/** The error state — `aria-invalid` flips the border to `--danger-600`. */
export const Invalid: Story = { args: { "aria-invalid": true } };
