import type { ReactNode } from "react";
import { cx } from "./cx";

type StatTone = "default" | "warn" | "danger";

export type StatItem = {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: StatTone;
};

const VALUE_TONE: Record<StatTone, string> = {
  default: "text-ink",
  warn: "text-warn",
  danger: "text-danger",
};

/**
 * Several headline numbers in one bar, separated by rules.
 * One surface instead of a row of identical cards.
 */
export function StatBar({
  items,
  className,
  label,
  flat = false,
}: {
  items: StatItem[];
  className?: string;
  label?: string;
  flat?: boolean;
}) {
  return (
    <dl
      aria-label={label}
      className={cx(
        // a 1px gap over the line colour draws the dividers for any column count
        "grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-line bg-line",
        !flat && "shadow-raised",
        items.length >= 4 ? "lg:grid-cols-4" : items.length === 3 ? "sm:grid-cols-3" : "",
        className,
      )}
    >
      {items.map((item, index) => (
        <div
          key={item.label}
          className={cx(
            "bg-surface px-5 py-4 sm:px-6 sm:py-5",
            items.length % 2 === 1 && index === items.length - 1 && "col-span-2 sm:col-span-1",
          )}
        >
          <dt className="text-[0.8125rem] font-medium text-ink-2">{item.label}</dt>
          <dd className={cx("mt-1 text-[1.75rem] font-semibold leading-none tabular-nums", VALUE_TONE[item.tone ?? "default"])}>
            {item.value}
          </dd>
          {item.hint ? <dd className="mt-1.5 text-[0.8125rem] leading-snug text-ink-2">{item.hint}</dd> : null}
        </div>
      ))}
    </dl>
  );
}

/** A single number with context, for metric pages where each value needs its own explanation. */
export function MetricCard({
  label,
  value,
  detail,
  visual,
}: {
  label: string;
  value: ReactNode;
  detail: ReactNode;
  visual?: ReactNode;
}) {
  return (
    <div className="flex gap-4 rounded-2xl border border-line bg-surface p-5 shadow-raised">
      {visual ? <div className="shrink-0">{visual}</div> : null}
      <dl className="min-w-0">
        <dt className="text-[0.8125rem] font-medium text-ink-2">{label}</dt>
        <dd className="mt-1 text-[1.75rem] font-semibold leading-none tabular-nums text-ink">{value}</dd>
        <dd className="mt-2 text-[0.8125rem] leading-snug text-ink-2">{detail}</dd>
      </dl>
    </div>
  );
}

/** Shown in place of a number that does not exist yet. */
export function NoValue() {
  return (
    <>
      <span aria-hidden="true">–</span>
      <span className="sr-only">No data yet</span>
    </>
  );
}
