import type { ReactNode } from "react";
import { cx } from "./cx";

export type Tone = "neutral" | "teal" | "solid" | "warn" | "danger" | "outline";

const TONE: Record<Tone, string> = {
  neutral: "bg-neutral-bg text-ink-2",
  teal: "bg-mint text-teal-text",
  solid: "bg-deep text-white",
  warn: "bg-warn-bg text-warn",
  danger: "bg-danger-bg text-danger",
  outline: "border border-line bg-surface text-ink-2",
};

/** A short status label. Colour is never the only signal: the words carry the meaning. */
export function Badge({
  tone = "neutral",
  icon,
  children,
  className,
}: {
  tone?: Tone;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[0.8125rem] font-medium leading-5",
        "[&_svg]:size-3.5 [&_svg]:shrink-0",
        TONE[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
