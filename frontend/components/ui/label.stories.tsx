import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Input } from "./input";
import { Label } from "./label";

/**
 * Label primitive — always tied to its control via `htmlFor`/`id` so screen
 * readers announce the field (architecture.md §8). Shown standalone and in the
 * canonical label+input pairing the auth forms use.
 */
const meta = {
  title: "UI/Label",
  component: Label,
  tags: ["autodocs"],
  parameters: { layout: "padded" },
  args: { children: "Email" },
} satisfies Meta<typeof Label>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};

/** The accessible pairing: clicking the label focuses the bound input. */
export const WithInput: Story = {
  render: () => (
    <div className="flex max-w-sm flex-col gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input id="email" type="email" placeholder="you@example.com" />
    </div>
  ),
};
