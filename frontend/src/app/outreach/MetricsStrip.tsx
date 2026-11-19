import { getMetrics } from "@/lib/outreach-api";

const CHANNEL_LABEL: Record<string, string> = {
  sms: "SMS reminder",
  call: "Phone call",
  home_visit: "Home visit (CHW)",
  coordinator: "Care coordinator",
};

const pct = (r: number | null) => (r === null ? null : `${Math.round(r * 100)}%`);
const days = (d: number | null) => (d === null ? null : `${d.toFixed(1)} days`);

function Card({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | null;
  detail: string;
}) {
  return (
    <div className="rounded-lg border border-black/10 p-4 dark:border-white/15">
      <dt className="text-sm text-neutral-600 dark:text-neutral-300">{label}</dt>
      <dd className="text-3xl font-semibold">
        {value ?? (
          <>
            <span aria-hidden="true">—</span>
            <span className="sr-only">No data yet</span>
          </>
        )}
      </dd>
      <dd className="mt-1 text-sm text-neutral-600 dark:text-neutral-300">{detail}</dd>
    </div>
  );
}

export async function MetricsStrip() {
  const m = await getMetrics();
  const lc = m.loop_closure;
  const esc = m.escalation;
  const ttr = m.time_to_referral;
  const noOutreach = lc.contacted_episodes === 0;
  const channelRows = Object.entries(CHANNEL_LABEL).map(([key, label]) => ({
    label,
    count: lc.attended_by_last_channel[key] ?? 0,
  }));

  return (
    <section aria-labelledby="metrics-heading" className="space-y-4">
      <h2 id="metrics-heading" className="text-lg font-medium">
        Loop-closure metrics
      </h2>
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card
          label="Loop closure rate"
          value={pct(lc.closure_rate)}
          detail={
            noOutreach
              ? "No outreach yet"
              : `${lc.attended} of ${lc.contacted_episodes} contacted episodes attended · ${lc.still_open} still open`
          }
        />
        <Card
          label="Escalation rate"
          value={pct(esc.escalation_rate)}
          detail={
            noOutreach
              ? "No outreach yet"
              : `${esc.escalated} of ${lc.contacted_episodes} episodes reached a coordinator`
          }
        />
        <Card
          label="Recovery after escalation"
          value={pct(esc.recovery_rate)}
          detail={
            esc.escalated === 0
              ? "No escalations yet"
              : `${esc.recovered} of ${esc.escalated} escalated episodes attended · ${esc.awaiting_coordinator} awaiting a coordinator`
          }
        />
        <Card
          label="Median time to referral"
          value={days(ttr.median_days)}
          detail={`${ttr.completed} completed · ${pct(ttr.within_sla_rate) ?? "n/a"} within the ${ttr.sla_days}-day target · ${ttr.awaiting} still waiting`}
        />
      </dl>

      {lc.unrecorded_advances > 0 && (
        <p
          role="note"
          className="rounded-md bg-amber-100 p-2 text-sm text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
        >
          Data quality: {lc.unrecorded_advances} contacted episode
          {lc.unrecorded_advances === 1 ? "" : "s"} moved on without a recorded response and{" "}
          {lc.unrecorded_advances === 1 ? "is" : "are"} not counted as attended.
        </p>
      )}

      <div className="space-y-2">
        <h3 className="font-medium">Attendance by most recent contact</h3>
        <p className="text-sm text-neutral-600 dark:text-neutral-300">
          {lc.attended === 0
            ? "No attendance after outreach recorded yet."
            : `Median contacts before attending: ${lc.median_contacts_to_attend}. ${lc.attended_without_outreach} patient${lc.attended_without_outreach === 1 ? "" : "s"} attended before any contact.`}
        </p>
        <ul className="space-y-1">
          {channelRows.map((row) => {
            const share = lc.attended > 0 ? (row.count / lc.attended) * 100 : 0;
            return (
              <li
                key={row.label}
                className="grid grid-cols-[10rem_1fr_2rem] items-center gap-3 text-sm"
              >
                <span>{row.label}</span>
                <div aria-hidden="true" className="h-2 rounded bg-black/10 dark:bg-white/15">
                  <div className="h-2 rounded bg-teal-700" style={{ width: `${share}%` }} />
                </div>
                <span className="text-right tabular-nums">{row.count}</span>
              </li>
            );
          })}
        </ul>
      </div>

      <p className="text-sm text-neutral-600 dark:text-neutral-300">{m.disclaimer}</p>

      <details className="rounded-md border border-black/10 p-3 text-sm dark:border-white/15">
        <summary className="cursor-pointer font-medium">How these are calculated</summary>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>
            An <strong>episode</strong> is one overdue stage of one case that received at least one
            contact.
          </li>
          <li>
            <strong>Loop closure rate</strong> = episodes that ended in a recorded attendance ÷ all
            contacted episodes. Episodes still in progress count in the denominator, so the rate is
            conservative.
          </li>
          <li>
            <strong>Escalation rate</strong> = episodes handed to a coordinator ÷ all contacted
            episodes. <strong>Recovery</strong> = those that later attended.
          </li>
          <li>
            <strong>Time to referral</strong> covers completed cases only (abnormal result to
            referral); cases still waiting are counted separately.
          </li>
          <li>
            Attendance after contact is an association, not proof that contact caused it. We
            deliberately do not compare contacted with uncontacted cases: outreach only starts once a
            case is already late.
          </li>
        </ul>
      </details>
    </section>
  );
}
