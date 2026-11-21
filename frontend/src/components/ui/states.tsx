import { Inbox } from "lucide-react";
import type { ReactNode } from "react";
import { cx } from "./cx";

/** What an empty list means, and what to do about it. */
export function EmptyState({
  icon,
  title,
  children,
  action,
  className,
}: {
  icon?: ReactNode;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cx(
        "flex flex-col items-center rounded-2xl border border-dashed border-line bg-surface/60 px-6 py-10 text-center",
        className,
      )}
    >
      <span className="flex size-11 items-center justify-center rounded-full bg-mint text-teal-text [&_svg]:size-5">
        {icon ?? <Inbox aria-hidden="true" />}
      </span>
      <p className="mt-3 font-semibold text-ink">{title}</p>
      {children ? <p className="mt-1 max-w-md text-sm text-ink-2">{children}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

/** Placeholder blocks shown while a page streams in. */
export function Skeleton({ className }: { className?: string }) {
  return <span aria-hidden="true" className={cx("block animate-pulse rounded-xl bg-line/70", className)} />;
}
