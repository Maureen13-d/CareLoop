import type { ReactNode } from "react";
import { cx } from "./cx";

/**
 * A white working surface. `tone="mint"` is for supporting, non-interactive context;
 * `tone="danger"` outlines a card that needs a person to act.
 */
export function Card({
  children,
  className,
  tone = "white",
  padded = true,
  as: Tag = "div",
  ...rest
}: {
  children: ReactNode;
  className?: string;
  tone?: "white" | "mint" | "danger";
  padded?: boolean;
  as?: "div" | "section" | "article" | "aside" | "li";
} & Record<`aria-${string}`, string | undefined>) {
  return (
    <Tag
      className={cx(
        "rounded-2xl border",
        tone === "mint" ? "border-mint-strong bg-mint" : "bg-surface shadow-raised",
        tone === "white" && "border-line",
        tone === "danger" && "border-danger/30",
        padded && "p-5 sm:p-6",
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}

/** Heading row for a card or page section, with an optional action on the right. */
export function SectionHeader({
  id,
  title,
  description,
  action,
  level = 2,
  className,
}: {
  id?: string;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  level?: 2 | 3;
  className?: string;
}) {
  const Heading = level === 2 ? "h2" : "h3";
  return (
    <div className={cx("flex flex-wrap items-start justify-between gap-x-4 gap-y-2", className)}>
      <div className="min-w-0 flex-1">
        <Heading id={id} className={level === 2 ? "text-lg" : "text-base"}>
          {title}
        </Heading>
        {description ? <p className="mt-1 text-sm text-ink-2">{description}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

/** A label and a value, for small key facts inside cards. */
export function KeyValue({ label, children }: { label: ReactNode; children: ReactNode }) {
  return (
    <div>
      <dt className="text-[0.8125rem] text-ink-2">{label}</dt>
      <dd className="mt-0.5 text-[0.9375rem] font-medium text-ink">{children}</dd>
    </div>
  );
}
