import { cx } from "./cx";

/** A ring showing a share out of 100. The number inside is the real value, not decoration. */
export function ProgressRing({
  percent,
  size = 96,
  label,
}: {
  percent: number | null;
  size?: number;
  label: string;
}) {
  const stroke = 9;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const value = percent == null ? 0 : Math.max(0, Math.min(100, percent));
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label={percent == null ? `${label}: no data yet` : `${label}: ${Math.round(value)}%`}
      className="shrink-0"
    >
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--mint-strong)" strokeWidth={stroke} />
      {value > 0 ? (
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--teal)"
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={`${(value / 100) * circumference} ${circumference}`}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      ) : null}
      <text
        x="50%"
        y="50%"
        dominantBaseline="central"
        textAnchor="middle"
        fill="var(--ink)"
        style={{ fontSize: size * 0.22, fontWeight: 600 }}
      >
        {percent == null ? "–" : `${Math.round(value)}%`}
      </text>
    </svg>
  );
}

/** A labelled horizontal bar for counts that share a scale. */
export function Meter({
  label,
  value,
  max,
  tone = "teal",
  className,
}: {
  label: string;
  value: number;
  max: number;
  tone?: "teal" | "deep" | "warn";
  className?: string;
}) {
  const share = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className={cx("grid grid-cols-[minmax(7rem,12rem)_1fr_2.5rem] items-center gap-3 text-sm", className)}>
      <span className="truncate text-ink">{label}</span>
      <span aria-hidden="true" className="h-2 overflow-hidden rounded-full bg-neutral-bg">
        <span
          className={cx("block h-full rounded-full", tone === "deep" ? "bg-deep" : tone === "warn" ? "bg-warn" : "bg-teal")}
          style={{ width: `${value > 0 ? Math.max(3, share) : 0}%` }}
        />
      </span>
      <span className="text-right font-medium tabular-nums text-ink">{value}</span>
    </div>
  );
}
