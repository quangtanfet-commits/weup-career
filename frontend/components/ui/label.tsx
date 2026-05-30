import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Label primitive (shadcn/ui pattern). Always tie a label to its control via
 * `htmlFor`/`id` so screen readers announce the field (architecture.md §8).
 */
export type LabelProps = React.LabelHTMLAttributes<HTMLLabelElement>;

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        "text-sm font-medium leading-none text-ink-900",
        className,
      )}
      {...props}
    />
  ),
);
Label.displayName = "Label";

export { Label };
