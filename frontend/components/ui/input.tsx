import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Input primitive (shadcn/ui pattern, code-in-repo per architecture.md §1).
 * Uses the `--radius-sm` + `--input` border tokens; the focus ring uses
 * `--ring` (≥3:1) for WCAG AA keyboard visibility (architecture.md §8).
 */
export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "flex h-10 w-full rounded-sm border border-input bg-white px-3 py-2 text-sm text-ink-900 placeholder:text-ink-600/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 aria-[invalid=true]:border-danger-600",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
