import { Meter } from "@/components/ui";

type Stage = { id: string; label: string; count: number };

/**
 * How many people are at each step of the pathway right now.
 * Columns on wide screens (read left to right like the journey), bars on phones.
 */
export function PathwayFunnel({ stages, caption }: { stages: Stage[]; caption: string }) {
  const max = Math.max(1, ...stages.map((stage) => stage.count));
  const total = stages.reduce((sum, stage) => sum + stage.count, 0);
  return (
    <figure>
      <figcaption className="sr-only">{caption}</figcaption>
      <ol className="hidden items-end gap-3 sm:flex" aria-label={caption}>
        {stages.map((stage, index) => (
          <li key={stage.id} className="flex min-w-0 flex-1 flex-col items-center">
            <span className="text-xl font-semibold tabular-nums text-ink">{stage.count}</span>
            <span aria-hidden="true" className="mt-2 flex h-28 w-full items-end rounded-t-lg bg-canvas">
              <span
                className={index === stages.length - 1 ? "w-full rounded-t-lg bg-deep" : "w-full rounded-t-lg bg-teal"}
                style={{ height: `${stage.count > 0 ? Math.max(6, (stage.count / max) * 100) : 0}%` }}
              />
            </span>
            <span className="mt-2 flex w-full items-start gap-1.5 border-t-2 border-line pt-2">
              <span className="text-[0.75rem] font-semibold tabular-nums text-ink-3">{index + 1}</span>
              <span className="text-[0.8125rem] leading-tight text-ink">{stage.label}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className="space-y-2.5 sm:hidden">
        {stages.map((stage) => (
          <Meter key={stage.id} label={stage.label} value={stage.count} max={max} />
        ))}
      </div>
      <p className="sr-only">{total} people across all steps.</p>
    </figure>
  );
}
