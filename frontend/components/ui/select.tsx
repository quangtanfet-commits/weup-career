import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Native `<select>` styled to the design tokens (architecture.md §2). A native
 * control is used in F1 for the few enum fields (school_level, user_type): it is
 * keyboard- and screen-reader-accessible out of the box (architecture.md §8) and
 * avoids pulling in a Radix listbox before a feature needs richer behaviour.
 */
export type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement>;

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        "flex h-10 w-full rounded-sm border border-input bg-white px-3 py-2 text-sm text-ink-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 aria-[invalid=true]:border-danger-600",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  ),
);
Select.displayName = "Select";

export { Select };
