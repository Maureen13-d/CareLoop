import type { ReactNode } from "react";
import { cx } from "./cx";

type TimelineTone = "default" | "ok" | "warn" | "danger";

const DOT: Record<TimelineTone, string> = {
  default: "border-teal bg-surface",
  ok: "border-teal bg-teal",
  warn: "border-warn bg-warn-bg",
  danger: "border-danger bg-danger",
};

/** A vertical record of what happened, newest or oldest first as the caller decides. */
export function Timeline({ children, label }: { children: ReactNode; label: string }) {
  return (
    <ol aria-label={label} className="relative space-y-5 before:absolute before:top-2 before:bottom-2 before:left-[0.4375rem] before:w-px before:bg-line">
      {children}
    </ol>
  );
}

export function TimelineItem({
  title,
  meta,
  tone = "default",
  children,
}: {
  title: ReactNode;
  meta?: ReactNode;
  tone?: TimelineTone;
  children?: ReactNode;
}) {
  return (
    <li className="relative pl-7">
      <span aria-hidden="true" className={cx("absolute top-1.5 left-0 size-[0.9375rem] rounded-full border-2", DOT[tone])} />
      <p className="text-[0.9375rem] font-medium text-ink">{title}</p>
      {meta ? <p className="mt-0.5 text-[0.8125rem] text-ink-2">{meta}</p> : null}
      {children ? <div className="mt-1.5 text-sm text-ink">{children}</div> : null}
    </li>
  );
}
