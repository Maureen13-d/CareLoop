import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { cx } from "./cx";

/** The top of every workspace page: where you are, what this page is for, what you can do. */
export function PageHeader({
  title,
  description,
  back,
  meta,
  actions,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  back?: { href: string; label: string };
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cx("space-y-3", className)}>
      {back ? (
        <Link
          href={back.href}
          className="inline-flex items-center gap-1.5 rounded-full text-sm font-medium text-teal-text hover:underline"
        >
          <ArrowLeft aria-hidden="true" className="size-4" />
          {back.label}
        </Link>
      ) : null}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0 max-w-3xl">
          <h1 className="text-[1.75rem] sm:text-[2rem]">{title}</h1>
          {description ? <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-2 sm:text-base">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
      {meta ? <div className="flex flex-wrap items-center gap-2">{meta}</div> : null}
    </header>
  );
}

/** Consistent page width and vertical rhythm for the workspace. */
export function Page({ children, narrow = false, className }: { children: ReactNode; narrow?: boolean; className?: string }) {
  return (
    <main
      id="content"
      tabIndex={-1}
      className={cx("mx-auto w-full space-y-6 px-4 py-6 outline-none sm:px-6 lg:px-10 lg:py-9", narrow ? "max-w-3xl" : "max-w-6xl", className)}
    >
      {children}
    </main>
  );
}
