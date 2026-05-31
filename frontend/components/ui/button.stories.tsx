import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Button } from "./button";

/**
 * Button primitive — every variant × size, plus the disabled and `asChild`
 * (render-as-link) states. Covers the full design-token surface so Chromatic
 * pins each visual variant.
 */
const meta = {
  title: "UI/Button",
  component: Button,
  tags: ["autodocs"],
  args: { children: "Đăng nhập" },
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "secondary", "outline", "ghost", "danger"],
    },
    size: { control: "select", options: ["default", "sm", "lg", "icon"] },
    disabled: { control: "boolean" },
  },
} satisfies Meta<typeof Button>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Secondary: Story = { args: { variant: "secondary" } };
export const Outline: Story = { args: { variant: "outline" } };
export const Ghost: Story = { args: { variant: "ghost" } };
export const Danger: Story = { args: { variant: "danger", children: "Xoá" } };

export const Small: Story = { args: { size: "sm" } };
export const Large: Story = { args: { size: "lg" } };

export const Disabled: Story = { args: { disabled: true } };

/** `asChild` renders the variant styles onto a real anchor (keyboard-navigable). */
export const AsLink: Story = {
  args: { asChild: true },
  render: (args) => (
    <Button {...args}>
      <a href="#dashboard">Tới trang chính</a>
    </Button>
  ),
};

/** All variants side by side — the canonical Chromatic snapshot. */
export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-3">
      <Button>Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="danger">Danger</Button>
    </div>
  ),
};
