import { cx } from "./cx";

/**
 * The CareLoop mark: a ring that is almost closed, with the person (the dot)
 * at the point where the loop closes.
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={cx("size-8 shrink-0", className)}>
      <path
        d="M24.5 7.5A12 12 0 1 0 28 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <circle cx="27.6" cy="9.6" r="3" fill="var(--teal)" />
    </svg>
  );
}

export function Wordmark({ className, tone = "dark" }: { className?: string; tone?: "dark" | "light" }) {
  return (
    <span className={cx("inline-flex items-center gap-2.5", tone === "light" ? "text-white" : "text-emerald", className)}>
      <BrandMark />
      <span className="text-lg font-semibold tracking-tight">CareLoop</span>
    </span>
  );
}

/** Initials in a circle, for staff and synthetic patients. */
export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
  return (
    <span
      aria-hidden="true"
      className={cx(
        "flex size-9 shrink-0 items-center justify-center rounded-full bg-mint text-[0.8125rem] font-semibold text-teal-text",
        className,
      )}
    >
      {initials || "?"}
    </span>
  );
}
