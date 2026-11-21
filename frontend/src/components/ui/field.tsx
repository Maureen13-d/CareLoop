import type { ComponentProps, ReactNode } from "react";
import { cx } from "./cx";

type ControlOptions = { size?: "sm" | "md" | "lg"; shape?: "box" | "pill"; width?: "full" | "auto" };

/**
 * Classes for a text input or select. Options replace the defaults rather than
 * being layered on top, so no two classes fight over the same property.
 */
export function controlClass({ size = "md", shape = "box", width = "full" }: ControlOptions = {}): string {
  return cx(
    "border border-control bg-surface text-ink placeholder:text-ink-3 transition-colors hover:border-ink-2",
    "focus-visible:border-teal focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-teal/40",
    "disabled:bg-neutral-bg",
    width === "full" ? "w-full" : "w-auto",
    size === "sm" && "min-h-9 text-sm",
    size === "md" && "min-h-11 text-[0.9375rem]",
    size === "lg" && "min-h-14 text-lg",
    shape === "pill" ? "rounded-full px-5" : size === "lg" ? "rounded-2xl px-4" : "rounded-xl px-3.5",
  );
}

/** The default control: medium, boxed, full width. */
export const controlClasses = controlClass();

/** A labelled form control with an optional hint below it. */
export function Field({
  label,
  hint,
  htmlFor,
  children,
  className,
}: {
  label: ReactNode;
  hint?: ReactNode;
  htmlFor: string;
  children: ReactNode;
  className?: string;
}) {
  const hintId = hint ? `${htmlFor}-hint` : undefined;
  return (
    <div className={cx("space-y-1.5", className)}>
      <label htmlFor={htmlFor} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {hint ? (
        <p id={hintId} className="text-[0.8125rem] leading-snug text-ink-2">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export function Input({ className, ...rest }: ComponentProps<"input">) {
  return <input className={cx(controlClasses, className)} {...rest} />;
}

export function Select({ className, ...rest }: ComponentProps<"select">) {
  return <select className={cx(controlClasses, className)} {...rest} />;
}

export function Textarea({ className, ...rest }: ComponentProps<"textarea">) {
  return <textarea className={cx(controlClass(), "py-2.5", className)} rows={4} {...rest} />;
}

/** A checkbox with its label and an optional explanation, as one large tap target. */
export function CheckField({
  label,
  description,
  className,
  ...rest
}: Omit<ComponentProps<"input">, "type"> & { label: ReactNode; description?: ReactNode }) {
  return (
    <label
      className={cx(
        "flex cursor-pointer items-start gap-3 rounded-xl border border-line bg-surface px-4 py-3",
        "has-[:checked]:border-teal has-[:checked]:bg-mint",
        className,
      )}
    >
      <input type="checkbox" className="mt-0.5 size-5 shrink-0 accent-deep" {...rest} />
      <span>
        <span className="block text-[0.9375rem] font-medium text-ink">{label}</span>
        {description ? <span className="mt-0.5 block text-sm text-ink-2">{description}</span> : null}
      </span>
    </label>
  );
}

/** Groups related fields under a short heading inside a form. */
export function FormSection({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <fieldset className={cx("space-y-4", className)}>
      <legend className="mb-1 text-base font-semibold text-ink">{title}</legend>
      {description ? <p className="-mt-2 text-sm text-ink-2">{description}</p> : null}
      {children}
    </fieldset>
  );
}
