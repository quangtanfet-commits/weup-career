import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { Button } from "./button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./card";

/**
 * Card primitives composed into the shapes the app actually uses: a full
 * header+content+footer surface, a header-only variant, and a content-only
 * variant. Mirrors the consent/wellbeing/recommendation card layouts.
 */
const meta = {
  title: "UI/Card",
  component: Card,
  tags: ["autodocs"],
  parameters: { layout: "padded" },
} satisfies Meta<typeof Card>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Full: Story = {
  render: () => (
    <Card className="max-w-md">
      <CardHeader>
        <CardTitle>Đồng ý của người giám hộ</CardTitle>
        <CardDescription>
          Tài khoản của người dưới 16 tuổi cần người giám hộ xác nhận trước khi
          sử dụng.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-ink-600">
          Vui lòng nhập thông tin người giám hộ để gửi yêu cầu đồng ý.
        </p>
      </CardContent>
      <CardFooter className="justify-end gap-2">
        <Button variant="outline">Huỷ</Button>
        <Button>Gửi yêu cầu</Button>
      </CardFooter>
    </Card>
  ),
};

export const HeaderOnly: Story = {
  render: () => (
    <Card className="max-w-md">
      <CardHeader>
        <CardTitle>Sức khoẻ tinh thần</CardTitle>
        <CardDescription>
          Nội dung hỗ trợ, không thay thế tư vấn lâm sàng.
        </CardDescription>
      </CardHeader>
    </Card>
  ),
};

export const ContentOnly: Story = {
  render: () => (
    <Card className="max-w-md">
      <CardContent className="pt-6">
        <p className="text-sm text-ink-900">
          Một thẻ chỉ có nội dung, dùng cho danh sách nghề nghiệp.
        </p>
      </CardContent>
    </Card>
  ),
};
