"use client";

import { LoaderCircle } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";
import { useFormStatus } from "react-dom";
import { buttonClasses, type ButtonSize, type ButtonVariant } from "./button";

/**
 * A form submit button that shows it is working while its server action runs,
 * and cannot be pressed twice.
 */
export function SubmitButton({
  children,
  pendingLabel,
  variant,
  size,
  block,
  className,
  disabled,
  ...rest
}: Omit<ComponentProps<"button">, "type"> & {
  pendingLabel?: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
}) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending || disabled}
      aria-busy={pending || undefined}
      className={buttonClasses({ variant, size, block, className })}
      {...rest}
    >
      {pending ? (
        <>
          <LoaderCircle aria-hidden="true" className="animate-spin" />
          {pendingLabel ?? children}
        </>
      ) : (
        children
      )}
    </button>
  );
}
