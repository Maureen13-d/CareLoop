import Link from "next/link";
import { cx } from "./cx";

/** Link-based filters. Each option is a real URL, so the view can be shared or reloaded. */
export function FilterTabs({
  label,
  items,
  active,
}: {
  label: string;
  items: { id: string; label: string; href: string; count?: number }[];
  active: string;
}) {
  return (
    <nav aria-label={label} className="-mx-1 overflow-x-auto px-1">
      <ul className="inline-flex gap-1 rounded-full border border-line bg-surface p-1">
        {items.map((item) => {
          const current = item.id === active;
          return (
            <li key={item.id}>
              <Link
                href={item.href}
                aria-current={current ? "page" : undefined}
                className={cx(
                  "inline-flex min-h-9 items-center gap-1.5 whitespace-nowrap rounded-full px-4 text-sm font-medium transition-colors",
                  current ? "bg-deep text-white" : "text-ink-2 hover:bg-mint hover:text-ink",
                )}
              >
                {item.label}
                {item.count !== undefined ? (
                  <span className={cx("tabular-nums", current ? "text-on-dark-2" : "text-ink-3")}>{item.count}</span>
                ) : null}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
