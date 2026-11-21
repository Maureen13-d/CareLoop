import type { ComponentProps, ReactNode } from "react";
import { cx } from "./cx";

/**
 * A data table on a white surface. It scrolls sideways inside its own frame on
 * narrow screens, so the page itself never scrolls horizontally.
 */
export function Table({
  caption,
  children,
  className,
}: {
  caption: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cx("overflow-x-auto rounded-2xl border border-line bg-surface shadow-raised", className)}>
      <table className="w-full border-collapse text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        {children}
      </table>
    </div>
  );
}

export function THead({ children }: { children: ReactNode }) {
  return (
    <thead className="border-b border-line bg-canvas/60 text-[0.8125rem] text-ink-2">
      <tr>{children}</tr>
    </thead>
  );
}

export function Th({ className, ...rest }: ComponentProps<"th">) {
  return <th scope="col" className={cx("whitespace-nowrap px-4 py-3 font-medium first:pl-5 last:pr-5", className)} {...rest} />;
}

export function Tr({ className, ...rest }: ComponentProps<"tr">) {
  return <tr className={cx("border-b border-line align-top last:border-0 hover:bg-canvas/50", className)} {...rest} />;
}

export function Td({ className, ...rest }: ComponentProps<"td">) {
  return <td className={cx("px-4 py-3.5 first:pl-5 last:pr-5", className)} {...rest} />;
}
