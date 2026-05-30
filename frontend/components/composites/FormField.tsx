import * as React from "react";

import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

/**
 * Composite that wires a label, an arbitrary control and an inline error message
 * together for accessibility (architecture.md §4.1, §8): the error node is
 * referenced via `aria-describedby` and the control is flagged `aria-invalid`
 * when an error is present, so screen readers announce the failure in Vietnamese
 * (RHF `errorMessage`). The control is cloned so callers pass any input element.
 */
export interface FormFieldProps {
  /** Stable id for the control; the label's `htmlFor` and `aria-describedby` derive from it. */
  readonly id: string;
  readonly label: string;
  readonly error?: string | undefined;
  /** Optional helper text rendered (and announced) under the control. */
  readonly hint?: string | undefined;
  readonly children: React.ReactElement;
  readonly className?: string;
}

export function FormField({
  id,
  label,
  error,
  hint,
  children,
  className,
}: FormFieldProps) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy =
    [error ? errorId : undefined, hint ? hintId : undefined]
      .filter(Boolean)
      .join(" ") || undefined;

  const control = React.cloneElement(
    children as React.ReactElement<{
      id?: string;
      "aria-invalid"?: boolean;
      "aria-describedby"?: string;
    }>,
    {
      id,
      "aria-invalid": error ? true : undefined,
      "aria-describedby": describedBy,
    },
  );

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor={id}>{label}</Label>
      {control}
      {hint ? (
        <p id={hintId} className="text-xs text-ink-600">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} role="alert" className="text-xs text-danger-600">
          {error}
        </p>
      ) : null}
    </div>
  );
}
