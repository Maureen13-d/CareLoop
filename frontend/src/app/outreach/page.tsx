export const instant = false;
import Link from "next/link";
import { getEvents, getQueue, type OutreachEvent } from "@/lib/outreach-api";
import { runSweep } from "./actions";
import { EscalatedSection } from "./EscalatedSection";
import { SweepButton } from "./SweepButton";

const CHANNEL_LABEL: Record<string, string> = {
  sms: "SMS reminder",
  call: "Phone call",
  home_visit: "Home visit (CHW)",
  coordinator: "Care coordinator",
  clinic: "Clinic visit",
};

const fmtStage = (s: string) => s.replace(/_/g, " ");
const fmtTime = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-black/10 p-4 dark:border-white/15">
      <dt className="text-sm text-neutral-600 dark:text-neutral-300">{label}</dt>
      <dd className="text-2xl font-semibold">{value}</dd>
    </div>
  );
}

function KindBadge({ kind }: { kind: OutreachEvent["kind"] }) {
  if (kind === "response") {
    return (
      <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-900 dark:bg-green-900/40 dark:text-green-100">
        Attended
      </span>
    );
  }
  return kind === "escalation" ? (
    <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-900 dark:bg-red-900/40 dark:text-red-100">
      Escalation
    </span>
  ) : (
    <span className="rounded bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-900 dark:bg-sky-900/40 dark:text-sky-100">
      Reminder
    </span>
  );
}

export default async function OutreachPage() {
  const [queue, events] = await Promise.all([getQueue(), getEvents(20)]);
  const escalations = queue.filter((p) => p.kind === "escalation").length;

  return (
    <main className="mx-auto max-w-5xl space-y-8 p-6 sm:p-8">
      <header className="space-y-3">
        <h1 className="text-2xl font-semibold">Outreach queue</h1>
        <p
          role="note"
          className="rounded-md bg-amber-100 p-2 text-sm text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
        >
          Synthetic data only. Contacts are simulated; nothing is actually sent.
        </p>
      </header>

      <section aria-labelledby="summary-heading">
        <h2 id="summary-heading" className="sr-only">
          Summary
        </h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Stat label="Cases due for outreach" value={queue.length} />
          <Stat label="Due for coordinator escalation" value={escalations} />
          <Stat label="Recent contacts logged" value={events.length} />
        </dl>
      </section>

      <section aria-labelledby="queue-heading" className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 id="queue-heading" className="text-lg font-medium">
            Next actions
          </h2>
          <form action={runSweep}>
            <SweepButton disabled={queue.length === 0} />
          </form>
        </div>

        {queue.length === 0 ? (
          <p>No outreach is due. Cases within their SLA, or contacted recently, are skipped.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Cases due for outreach, most overdue first</caption>
              <thead>
                <tr className="border-b border-black/10 dark:border-white/15">
                  <th scope="col" className="py-2 pr-4">Case</th>
                  <th scope="col" className="pr-4">Patient</th>
                  <th scope="col" className="pr-4">Stage</th>
                  <th scope="col" className="pr-4">Days overdue</th>
                  <th scope="col" className="pr-4">Next action</th>
                  <th scope="col">Message</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((p) => (
                  <tr key={p.case_id} className="border-b border-black/10 align-top dark:border-white/15">
                    <td className="py-2 pr-4">
                      <Link href={`/cases/${p.case_id}`} className="underline underline-offset-2">
                        {p.case_id}
                      </Link>
                    </td>
                    <td className="pr-4">{p.patient_ref}</td>
                    <td className="pr-4 capitalize">{fmtStage(p.stage)}</td>
                    <td className="pr-4">{p.days_overdue}</td>
                    <td className="space-x-2 pr-4">
                      <KindBadge kind={p.kind} />
                      <span>
                        {CHANNEL_LABEL[p.channel]} (attempt {p.attempt})
                      </span>
                    </td>
                    <td>{p.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <EscalatedSection />

      <section aria-labelledby="log-heading" className="space-y-3">
        <h2 id="log-heading" className="text-lg font-medium">
          Contact log
        </h2>
        {events.length === 0 ? (
          <p>No contacts yet. Run a sweep to generate the first batch.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Most recent outreach contacts, newest first</caption>
              <thead>
                <tr className="border-b border-black/10 dark:border-white/15">
                  <th scope="col" className="py-2 pr-4">Time (UTC)</th>
                  <th scope="col" className="pr-4">Case</th>
                  <th scope="col" className="pr-4">Patient</th>
                  <th scope="col" className="pr-4">Action</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id} className="border-b border-black/10 dark:border-white/15">
                    <td className="py-2 pr-4">
                      <time dateTime={e.created_at}>{fmtTime(e.created_at)}</time>
                    </td>
                    <td className="pr-4">
                      <Link href={`/cases/${e.case_id}`} className="underline underline-offset-2">
                        {e.case_id}
                      </Link>
                    </td>
                    <td className="pr-4">{e.patient_ref}</td>
                    <td className="space-x-2 pr-4">
                      <KindBadge kind={e.kind} />
                      <span>
                        {CHANNEL_LABEL[e.channel]} (attempt {e.attempt})
                      </span>
                    </td>
                    <td>{e.status.replace(/_/g, " ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
