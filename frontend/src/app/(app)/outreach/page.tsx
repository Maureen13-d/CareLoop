export const instant = false;
import { CircleCheck, MessageSquareText } from "lucide-react";
import Link from "next/link";
import { CHANNEL_LABEL, KindBadge, fmtStage, fmtTime } from "@/components/OutreachKind";
import {
  Badge,
  Banner,
  EmptyState,
  Page,
  PageHeader,
  SectionHeader,
  StatBar,
  Table,
  Td,
  Th,
  THead,
  Tr,
} from "@/components/ui";
import { getEvents, getQueue } from "@/lib/outreach-api";
import { runSweep } from "./actions";
import { EscalatedSection } from "./EscalatedSection";
import { MetricsStrip } from "./MetricsStrip";
import { SweepButton } from "./SweepButton";

export default async function OutreachPage() {
  const [queue, events] = await Promise.all([getQueue(), getEvents(20)]);
  const escalations = queue.filter((p) => p.kind === "escalation").length;

  return (
    <Page>
      <PageHeader
        title="Follow-up ladder"
        description="Simulated reminders for journeys that have gone quiet: a text first, then a call, a home visit, and finally a care coordinator."
        meta={<Badge tone="outline">Simulated, nothing is sent</Badge>}
      />
      <Banner>
        Synthetic data only. Contacts are simulated; nothing is actually sent. Pathway timings are unreviewed placeholders
        pending clinical review.
      </Banner>

      <StatBar
        label="Outreach summary"
        items={[
          { label: "Cases due for outreach", value: queue.length, tone: queue.length ? "warn" : "default" },
          { label: "Due for coordinator escalation", value: escalations, tone: escalations ? "danger" : "default" },
          { label: "Recent contacts logged", value: events.length },
        ]}
      />

      <section aria-labelledby="queue-heading" className="space-y-3">
        <SectionHeader
          id="queue-heading"
          title="Next actions"
          description="Most overdue first. A sweep logs the next contact for every case below."
          action={
            <form action={runSweep}>
              <SweepButton disabled={queue.length === 0} />
            </form>
          }
        />

        {queue.length === 0 ? (
          <EmptyState icon={<CircleCheck aria-hidden="true" />} title="No outreach is due">
            Cases within their target time, or contacted recently, are skipped.
          </EmptyState>
        ) : (
          <>
            <Table caption="Cases due for outreach, most overdue first" className="hidden md:block">
              <THead>
                <Th>Case</Th>
                <Th>Stage</Th>
                <Th>Overdue</Th>
                <Th>Next action</Th>
                <Th>Message</Th>
              </THead>
              <tbody>
                {queue.map((p) => (
                  <Tr key={p.case_id}>
                    <Td>
                      <Link href={`/cases/${p.case_id}`} className="font-medium text-teal-text hover:underline">
                        {p.case_id}
                      </Link>
                      <span className="mt-0.5 block text-ink-2">{p.patient_ref}</span>
                    </Td>
                    <Td className="whitespace-nowrap">{fmtStage(p.stage)}</Td>
                    <Td className="whitespace-nowrap">
                      <span className="font-medium tabular-nums text-warn">{p.days_overdue}</span>{" "}
                      <span className="text-ink-2">days</span>
                    </Td>
                    <Td>
                      <span className="flex flex-col items-start gap-1">
                        <KindBadge kind={p.kind} />
                        <span className="whitespace-nowrap text-ink">
                          {CHANNEL_LABEL[p.channel]}, attempt {p.attempt}
                        </span>
                      </span>
                    </Td>
                    <Td className="max-w-sm text-ink-2">{p.message}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>

            <ul className="space-y-3 md:hidden">
              {queue.map((p) => (
                <li key={p.case_id} className="rounded-2xl border border-line bg-surface p-4 shadow-raised">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <Link href={`/cases/${p.case_id}`} className="font-medium text-teal-text hover:underline">
                        {p.case_id}
                      </Link>
                      <p className="text-sm text-ink-2">
                        {p.patient_ref}, {fmtStage(p.stage).toLowerCase()}
                      </p>
                    </div>
                    <Badge tone="warn">{p.days_overdue} days over</Badge>
                  </div>
                  <p className="mt-3 flex flex-wrap items-center gap-2 text-sm text-ink">
                    <KindBadge kind={p.kind} />
                    {CHANNEL_LABEL[p.channel]}, attempt {p.attempt}
                  </p>
                  <p className="mt-2 flex gap-2 rounded-xl bg-canvas px-3 py-2 text-sm text-ink-2">
                    <MessageSquareText aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
                    {p.message}
                  </p>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <MetricsStrip />

      <EscalatedSection />

      <section aria-labelledby="log-heading" className="space-y-3">
        <SectionHeader id="log-heading" title="Contact log" description="The 20 most recent contacts, newest first." />
        {events.length === 0 ? (
          <EmptyState title="No contacts yet">Run a sweep to generate the first batch.</EmptyState>
        ) : (
          <Table caption="Most recent outreach contacts, newest first">
            <THead>
              <Th>Time (UTC)</Th>
              <Th>Case</Th>
              <Th>Action</Th>
              <Th>Status</Th>
            </THead>
            <tbody>
              {events.map((e) => (
                <Tr key={e.id}>
                  <Td className="whitespace-nowrap text-ink-2">
                    <time dateTime={e.created_at}>{fmtTime(e.created_at)}</time>
                  </Td>
                  <Td>
                    <Link href={`/cases/${e.case_id}`} className="font-medium text-teal-text hover:underline">
                      {e.case_id}
                    </Link>
                    <span className="mt-0.5 block text-ink-2">{e.patient_ref}</span>
                  </Td>
                  <Td>
                    <span className="flex flex-wrap items-center gap-2">
                      <KindBadge kind={e.kind} />
                      <span className="whitespace-nowrap">
                        {CHANNEL_LABEL[e.channel]}, attempt {e.attempt}
                      </span>
                    </span>
                  </Td>
                  <Td className="whitespace-nowrap">{fmtStage(e.status)}</Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </section>
    </Page>
  );
}
