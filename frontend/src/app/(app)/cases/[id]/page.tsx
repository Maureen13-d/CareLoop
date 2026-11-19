export const instant = false;
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  STAGES,
  getCaseDetail,
  type CaseStatus,
  type OutreachEvent,
  type Stage,
} from "@/lib/outreach-api";
import { markAttended } from "./actions";
import { AttendedButton } from "./AttendedButton";

const STATUS: Record<CaseStatus, { label: string; blurb: string; classes: string }> = {
  on_track: {
    label: "On track",
    blurb: "Within the expected timeframe for this stage.",
    classes: "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-100",
  },
  overdue: {
    label: "Overdue",
    blurb: "Past the target timeframe. Automated outreach is in progress.",
    classes: "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100",
  },
  escalated: {
    label: "Escalated",
    blurb: "Automated outreach is exhausted. A care coordinator needs to step in.",
    classes: "bg-red-100 text-red-900 dark:bg-red-900/40 dark:text-red-100",
  },
  closed: {
    label: "Closed",
    blurb: "This case has finished the pathway.",
    classes: "bg-neutral-200 text-neutral-900 dark:bg-neutral-700 dark:text-neutral-100",
  },
};

const CHANNEL_LABEL: Record<string, string> = {
  sms: "SMS reminder",
  call: "Phone call",
  home_visit: "Home visit (CHW)",
  coordinator: "Escalated to care coordinator",
  clinic: "Clinic visit",
};

const fmtStage = (s: string) => s.replace(/_/g, " ");
const fmtTime = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });

function eventTitle(e: OutreachEvent): string {
  if (e.kind === "response") {
    return `Patient attended (after ${e.attempt} outreach contact${e.attempt === 1 ? "" : "s"})`;
  }
  return `${CHANNEL_LABEL[e.channel]} · attempt ${e.attempt}`;
}

export default async function CasePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ attended?: string }>;
}) {
  const { id } = await params;
  const { attended } = await searchParams;
  const detail = await getCaseDetail(id);
  if (!detail) notFound();

  const { case: c, status, next_stages: nextStages, events } = detail;
  const s = STATUS[status];
  const visited = new Set<Stage>(c.history.map((h) => h.stage));
  const justAttended = attended && STAGES.includes(attended as Stage) ? attended : null;

  return (
    <main className="mx-auto max-w-3xl space-y-8 p-6 sm:p-8">
      <nav aria-label="Breadcrumb">
        <Link href="/outreach" className="text-sm underline underline-offset-2">
          ← Back to outreach queue
        </Link>
      </nav>

      <p
        role="note"
        className="rounded-md bg-amber-100 p-2 text-sm text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
      >
        Synthetic data only. Contacts are simulated; nothing is actually sent. Pathway timings are unreviewed placeholders pending clinical review.
      </p>

      {justAttended && (
        <div
          role="status"
          className="rounded-md border border-green-700 bg-green-50 p-4 text-green-950 dark:bg-green-900/30 dark:text-green-50"
        >
          <strong>Loop closed.</strong> The patient attended and the case moved to{" "}
          {fmtStage(justAttended)}. The outreach ladder has been reset for this stage.
        </div>
      )}

      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">
          Case {c.id} <span className="font-normal">· {c.patient_ref}</span>
        </h1>
        <div className="flex flex-wrap items-center gap-3">
          <span className={`rounded-full px-3 py-1 text-sm font-medium ${s.classes}`}>
            {s.label}
          </span>
          <span className="text-sm text-neutral-600 dark:text-neutral-300">{s.blurb}</span>
        </div>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">
          In <span className="capitalize">{fmtStage(c.stage)}</span> since{" "}
          <time dateTime={c.stage_entered_at}>{fmtTime(c.stage_entered_at)} UTC</time>
        </p>
      </header>

      <section aria-labelledby="progress-heading" className="space-y-3">
        <h2 id="progress-heading" className="text-lg font-medium">
          Pathway progress
        </h2>
        <ol aria-label="Care pathway stages" className="flex flex-wrap gap-2 text-sm">
          {STAGES.map((stage) => {
            const isCurrent = stage === c.stage;
            const isDone = visited.has(stage) && !isCurrent;
            const style = isCurrent
              ? "border-teal-700 bg-teal-700 text-white"
              : isDone
                ? "border-green-700 text-green-900 dark:text-green-100"
                : "border-black/20 text-neutral-600 dark:border-white/25 dark:text-neutral-300";
            return (
              <li
                key={stage}
                aria-current={isCurrent ? "step" : undefined}
                className={`rounded-full border px-3 py-1 capitalize ${style}`}
              >
                {isDone && <span aria-hidden="true">✓ </span>}
                {fmtStage(stage)}
                {isDone && <span className="sr-only"> (completed)</span>}
              </li>
            );
          })}
        </ol>
      </section>

      <section aria-labelledby="action-heading" className="space-y-3">
        <h2 id="action-heading" className="text-lg font-medium">
          Record patient attendance
        </h2>
        {nextStages.length === 0 ? (
          <p>This case is closed. No further action is needed.</p>
        ) : (
          <>
            <p>
              {nextStages.length > 1
                ? "The next step depends on the outcome of the visit. Choose one:"
                : "Confirm that the patient attended. The case will advance and the outreach ladder will reset."}
            </p>
            <div className="flex flex-wrap gap-3">
              {nextStages.map((next) => (
                <form key={next} action={markAttended}>
                  <input type="hidden" name="caseId" value={c.id} />
                  <input type="hidden" name="toStage" value={next} />
                  <AttendedButton label={`Patient attended → ${fmtStage(next)}`} />
                </form>
              ))}
            </div>
          </>
        )}
      </section>

      <section aria-labelledby="timeline-heading" className="space-y-3">
        <h2 id="timeline-heading" className="text-lg font-medium">
          Outreach timeline
        </h2>
        {events.length === 0 ? (
          <p>No outreach recorded yet.</p>
        ) : (
          <ol className="space-y-4 border-l border-black/15 pl-4 dark:border-white/20">
            {events.map((e) => (
              <li
                key={e.id}
                className={
                  e.kind === "response"
                    ? "rounded-md bg-green-50 p-3 dark:bg-green-900/30"
                    : e.kind === "escalation"
                      ? "rounded-md bg-red-50 p-3 dark:bg-red-900/30"
                      : "p-3"
                }
              >
                <p className="font-medium">{eventTitle(e)}</p>
                <p className="text-sm text-neutral-600 dark:text-neutral-300">
                  <time dateTime={e.created_at}>{fmtTime(e.created_at)} UTC</time> ·{" "}
                  <span className="capitalize">{fmtStage(e.stage)}</span> stage
                </p>
                <p className="text-sm">{e.message}</p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}
