"use client";

import { RefreshCw, Unplug } from "lucide-react";
import { buttonClasses } from "./button";

/** The body of an `error.tsx` boundary: says what failed and offers a retry. */
export function ErrorPanel({
  title,
  message,
  reset,
}: {
  title: string;
  message: string;
  reset: () => void;
}) {
  return (
    <main id="content" className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-6 lg:px-10">
      <div className="rounded-2xl border border-line bg-surface p-8 text-center shadow-raised">
        <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-danger-bg text-danger">
          <Unplug aria-hidden="true" className="size-5" />
        </span>
        <h1 className="mt-4 text-xl">{title}</h1>
        <p role="alert" className="mx-auto mt-2 max-w-md text-[0.9375rem] text-ink-2">
          {message}
        </p>
        <button type="button" onClick={reset} className={buttonClasses({ variant: "secondary", className: "mt-6" })}>
          <RefreshCw aria-hidden="true" />
          Try again
        </button>
      </div>
    </main>
  );
}
