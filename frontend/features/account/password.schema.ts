import { z } from "zod";

import type { PasswordChangeRequest } from "@/lib/api/endpoints/account";

/**
 * Change-password schema (architecture.md §11; FR-91). The backend
 * `PasswordChangeRequest` body is `{ current_password, new_password }`; the
 * form adds a client-side `confirm_password` so the user cannot mistype the new
 * secret. The backend remains the authority on the current password and on the
 * full password policy — the FE only enforces a usable minimum length and that
 * the confirmation matches.
 */
export const PASSWORD_MIN_LENGTH = 8;

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Hãy nhập mật khẩu hiện tại"),
    new_password: z
      .string()
      .min(
        PASSWORD_MIN_LENGTH,
        `Mật khẩu mới tối thiểu ${PASSWORD_MIN_LENGTH} ký tự`,
      ),
    confirm_password: z.string().min(1, "Hãy xác nhận mật khẩu mới"),
  })
  .refine((values) => values.new_password === values.confirm_password, {
    path: ["confirm_password"],
    message: "Mật khẩu xác nhận chưa khớp",
  });

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

export function toPasswordChangePayload(
  values: ChangePasswordFormValues,
): PasswordChangeRequest {
  return {
    current_password: values.current_password,
    new_password: values.new_password,
  };
}
