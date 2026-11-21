import { CircleCheck, CircleExclamationPoint, FlaskConical, Info } from "lucide-react";
import type { ReactNode } from "react";
import { cx } from "./cx";

type NoticeTone = "ok" | "bad" | "warn" | "info";

const STYLE: Record<NoticeTone, string> = {
  ok: "border-teal/30 bg-mint text-teal-text",
  bad: "border-danger/30 bg-danger-bg text-danger",
  warn: "border-warn/25 bg-warn-bg text-warn",
  info: "border-line bg-surface text-ink-2",
};

const ICON: Record<NoticeTone, ReactNode> = {
  ok: <CircleCheck aria-hidden="true" />,
  bad: <CircleExclamationPoint aria-hidden="true" />,
  warn: <CircleExclamationPoint aria-hidden="true" />,
  info: <Info aria-hidden="true" />,
};

/** Feedback after an action, or a standing note. Errors are announced to screen readers. */
export function Notice({
  tone,
  title,
  children,
  className,
}: {
  tone: NoticeTone;
  title?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div
      role={tone === "bad" ? "alert" : "status"}
      className={cx(
        "flex gap-3 rounded-xl border px-4 py-3 text-sm leading-relaxed [&>svg]:mt-0.5 [&>svg]:size-[1.125rem] [&>svg]:shrink-0",
        STYLE[tone],
        className,
      )}
    >
      {ICON[tone]}
      <div className="min-w-0">
        {title ? <p className="font-semibold">{title}</p> : null}
        {children ? <div className={title ? "mt-0.5" : undefined}>{children}</div> : null}
      </div>
    </div>
  );
}

/** The standing reminder that everything on screen is synthetic or simulated. */
export function Banner({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p
      role="note"
      className={cx(
        "flex gap-3 rounded-xl border border-warn/20 bg-warn-bg px-4 py-3 text-sm leading-relaxed text-warn",
        className,
      )}
    >
      <FlaskConical aria-hidden="true" className="mt-0.5 size-[1.125rem] shrink-0" />
      <span>{children}</span>
    </p>
  );
}
