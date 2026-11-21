import { Check } from "lucide-react";
import { cx } from "./cx";

type Step = { id: string; label: string };

/**
 * Where a person is on their pathway. A full stepper on wide screens; on phones a
 * compact bar with the current and next step, so it never needs sideways scrolling.
 * `finished` marks every step done (for closed journeys that left the main sequence).
 */
export function JourneyStepper({
  steps,
  current,
  finished = false,
  label = "Pathway progress",
}: {
  steps: Step[];
  current: string;
  finished?: boolean;
  label?: string;
}) {
  const here = finished ? steps.length : steps.findIndex((step) => step.id === current);
  const position = here === -1 ? 0 : here;
  const now = steps[position];
  const next = steps[position + 1];

  return (
    <div>
      {/* phones and small tablets */}
      <div className="md:hidden">
        <p className="text-sm text-ink-2">
          {finished ? "Journey finished" : now ? `Step ${position + 1} of ${steps.length}` : "Not on the main pathway"}
        </p>
        <p className="mt-0.5 font-semibold text-ink">{finished ? "All steps complete" : now?.label}</p>
        <JourneyMeter total={steps.length} reached={finished ? steps.length : position + 1} className="mt-3" />
        {!finished && next ? <p className="mt-2 text-sm text-ink-2">Next: {next.label}</p> : null}
      </div>

      {/* wider screens */}
      <ol aria-label={label} className="hidden md:flex">
        {steps.map((step, index) => {
          const done = index < here;
          const isCurrent = index === here && !finished;
          return (
            <li
              key={step.id}
              aria-current={isCurrent ? "step" : undefined}
              className="relative flex min-w-0 flex-1 flex-col items-center text-center"
            >
              {index > 0 ? (
                <span
                  aria-hidden="true"
                  className={cx("absolute top-[0.9375rem] right-1/2 h-0.5 w-full", index <= here ? "bg-teal" : "bg-line")}
                />
              ) : null}
              <span
                className={cx(
                  "relative z-10 flex size-8 items-center justify-center rounded-full border-2 text-[0.8125rem] font-semibold",
                  done && "border-teal bg-teal text-white",
                  isCurrent && "border-deep bg-deep text-white ring-4 ring-mint-strong",
                  !done && !isCurrent && "border-line bg-surface text-ink-3",
                )}
              >
                {done ? <Check aria-hidden="true" className="size-4" /> : index + 1}
              </span>
              <span
                className={cx(
                  "mt-2 px-1 text-[0.8125rem] leading-tight",
                  isCurrent ? "font-semibold text-ink" : done ? "text-ink" : "text-ink-2",
                )}
              >
                {step.label}
                {done ? <span className="sr-only"> (done)</span> : null}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

/** A small segmented bar: how many steps of a journey have been reached. */
export function JourneyMeter({ total, reached, className }: { total: number; reached: number; className?: string }) {
  return (
    <div
      role="img"
      aria-label={`Step ${Math.min(reached, total)} of ${total}`}
      className={cx("flex gap-1", className)}
    >
      {Array.from({ length: total }, (_, index) => (
        <span
          key={index}
          className={cx("h-1.5 flex-1 rounded-full", index < reached ? (index === reached - 1 ? "bg-deep" : "bg-teal") : "bg-line")}
        />
      ))}
    </div>
  );
}
