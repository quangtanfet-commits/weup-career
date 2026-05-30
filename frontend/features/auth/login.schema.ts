import { z } from "zod";

import type { components } from "@/lib/api/schema";

/**
 * Login schema — minimal client-side validation (architecture.md §1, Luồng 1).
 * Email is trimmed/lowercased to match the backend's normalisation; password is
 * only checked for presence here (the credential check is the backend's job).
 */
export const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .toLowerCase()
    .min(1, "Vui lòng nhập email")
    .email("Email không hợp lệ"),
  password: z.string().min(1, "Vui lòng nhập mật khẩu"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export type LoginPayload = components["schemas"]["LoginRequest"];

export function toLoginPayload(values: LoginFormValues): LoginPayload {
  return { email: values.email, password: values.password };
}
