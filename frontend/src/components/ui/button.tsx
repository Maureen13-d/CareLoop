import Link from "next/link";
import type { ComponentProps } from "react";
import { cx } from "./cx";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "on-dark" | "on-dark-outline";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANT: Record<ButtonVariant, string> = {
  primary: "bg-deep text-white hover:bg-emerald active:bg-emerald-2",
  secondary: "border border-line bg-surface text-ink hover:border-teal hover:bg-mint",
  ghost: "text-teal-text hover:bg-mint",
  danger: "border border-danger/30 bg-surface text-danger hover:bg-danger-bg",
  "on-dark": "bg-on-dark text-emerald hover:bg-white",
  "on-dark-outline": "border border-white/30 text-white hover:border-white/50 hover:bg-white/10",
};

const SIZE: Record<ButtonSize, string> = {
  sm: "min-h-9 px-3.5 text-sm gap-1.5",
  md: "min-h-11 px-5 text-[0.9375rem] gap-2",
  lg: "min-h-13 px-6 text-base gap-2",
};

export function buttonClasses({
  variant = "primary",
  size = "md",
  block = false,
  className,
}: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
  className?: string;
} = {}): string {
  return cx(
    "inline-flex items-center justify-center rounded-full font-medium transition-colors",
    "disabled:cursor-not-allowed disabled:opacity-55 [&_svg]:size-4 [&_svg]:shrink-0",
    VARIANT[variant],
    SIZE[size],
    block && "w-full",
    className,
  );
}

type ButtonProps = ComponentProps<"button"> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
};

export function Button({ variant, size, block, className, type = "submit", ...rest }: ButtonProps) {
  return <button type={type} className={buttonClasses({ variant, size, block, className })} {...rest} />;
}

type ButtonLinkProps = ComponentProps<typeof Link> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  block?: boolean;
};

export function ButtonLink({ variant = "secondary", size, block, className, ...rest }: ButtonLinkProps) {
  return <Link className={buttonClasses({ variant, size, block, className })} {...rest} />;
}
