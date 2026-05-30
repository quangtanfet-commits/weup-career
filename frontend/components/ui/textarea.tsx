import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Textarea primitive (shadcn/ui pattern, code-in-repo per architecture.md §1).
 * Mirrors the `Input` styling — `--radius-sm` + `--input` border, `--ring`
 * focus ring (≥3:1) for WCAG AA keyboard visibility (architecture.md §8) — for
 * multi-line free-text fields (e.g. the wellbeing support-request message).
 */
export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-24 w-full rounded-sm border border-input bg-white px-3 py-2 text-sm text-ink-900 placeholder:text-ink-600/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 aria-[invalid=true]:border-danger-600",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";

export { Textarea };
