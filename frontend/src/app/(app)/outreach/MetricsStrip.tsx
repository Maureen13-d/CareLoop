import { Card, Meter, MetricCard, Notice, NoValue, ProgressRing, SectionHeader } from "@/components/ui";
import { getMetrics } from "@/lib/outreach-api";

const CHANNEL_LABEL: Record<string, string> = {
  sms: "SMS reminder",
  call: "Phone call",
  home_visit: "Home visit (CHW)",
  coordinator: "Care coordinator",
};

const pct = (r: number | null) => (r === null ? null : `${Math.round(r * 100)}%`);
const days = (d: number | null) => (d === null ? null : `${d.toFixed(1)} days`);

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
  // bars show each channel's share of all attendances, as before
  const channelMax = Math.max(1, lc.attended);

  return (
    <section aria-labelledby="metrics-heading" className="space-y-4">
      <SectionHeader id="metrics-heading" title="Loop-closure metrics" description={m.disclaimer} />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Loop closure rate"
          value={pct(lc.closure_rate) ?? <NoValue />}
          visual={<ProgressRing percent={lc.closure_rate === null ? null : lc.closure_rate * 100} size={56} label="Loop closure rate" />}
          detail={
            noOutreach
              ? "No outreach yet"
              : `${lc.attended} of ${lc.contacted_episodes} contacted episodes attended. ${lc.still_open} still open.`
          }
        />
        <MetricCard
          label="Escalation rate"
          value={pct(esc.escalation_rate) ?? <NoValue />}
          detail={
            noOutreach ? "No outreach yet" : `${esc.escalated} of ${lc.contacted_episodes} episodes reached a coordinator.`
          }
        />
        <MetricCard
          label="Recovery after escalation"
          value={pct(esc.recovery_rate) ?? <NoValue />}
          detail={
            esc.escalated === 0
              ? "No escalations yet"
              : `${esc.recovered} of ${esc.escalated} escalated episodes attended. ${esc.awaiting_coordinator} awaiting a coordinator.`
          }
        />
        <MetricCard
          label="Median time to referral"
          value={days(ttr.median_days) ?? <NoValue />}
          detail={`${ttr.completed} completed, ${pct(ttr.within_sla_rate) ?? "n/a"} within the ${ttr.sla_days}-day target. ${ttr.awaiting} still waiting.`}
        />
      </div>

      {lc.unrecorded_advances > 0 && (
        <Notice tone="warn" title="Data quality">
          {lc.unrecorded_advances} contacted episode{lc.unrecorded_advances === 1 ? "" : "s"} moved on without a recorded
          response and {lc.unrecorded_advances === 1 ? "is" : "are"} not counted as attended.
        </Notice>
      )}

      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card>
          <SectionHeader
            level={3}
            title="Attendance by most recent contact"
            description={
              lc.attended === 0
                ? "No attendance after outreach recorded yet."
                : `Median contacts before attending: ${lc.median_contacts_to_attend}. ${lc.attended_without_outreach} patient${lc.attended_without_outreach === 1 ? "" : "s"} attended before any contact.`
            }
          />
          <div className="mt-4 space-y-2.5">
            {channelRows.map((row) => (
              <Meter key={row.label} label={row.label} value={row.count} max={channelMax} />
            ))}
          </div>
        </Card>

        <Card tone="mint">
          <details className="group text-sm">
            <summary className="cursor-pointer list-none font-semibold text-ink [&::-webkit-details-marker]:hidden">
              <span className="inline-flex items-center gap-2">
                <span aria-hidden="true" className="inline-block transition-transform group-open:rotate-90">
                  ›
                </span>
                How these are calculated
              </span>
            </summary>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-ink-2">
              <li>
                An <strong className="text-ink">episode</strong> is one overdue stage of one case that received at least one
                contact.
              </li>
              <li>
                <strong className="text-ink">Loop closure rate</strong> = episodes that ended in a recorded attendance ÷ all
                contacted episodes. Episodes still in progress count in the denominator, so the rate is conservative.
              </li>
              <li>
                <strong className="text-ink">Escalation rate</strong> = episodes handed to a coordinator ÷ all contacted
                episodes. <strong className="text-ink">Recovery</strong> = those that later attended.
              </li>
              <li>
                <strong className="text-ink">Time to referral</strong> covers completed cases only (abnormal result to
                referral); cases still waiting are counted separately.
              </li>
              <li>
                Attendance after contact is an association, not proof that contact caused it. We deliberately do not compare
                contacted with uncontacted cases: outreach only starts once a case is already late.
              </li>
            </ul>
          </details>
        </Card>
      </div>
    </section>
  );
}
