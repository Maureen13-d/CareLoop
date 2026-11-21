import { CircleCheck, DoorOpen, UserX } from "lucide-react";
import { redirect } from "next/navigation";
import {
  Badge,
  Card,
  EmptyState,
  Meter,
  MetricCard,
  Page,
  PageHeader,
  ProgressRing,
  SectionHeader,
  Table,
  Td,
  Th,
  THead,
  Tr,
} from "@/components/ui";
import { SubmitButton } from "@/components/ui/submit-button";
import { api } from "@/lib/api";
import { stageShort } from "@/lib/format";
import { sentence } from "@/lib/status";
import { getSession } from "@/lib/session";
import { markArrived, markLost } from "./actions";

export const instant = false;

type Summary = {
  synthetic: boolean;
  review: string;
  funnel: Record<string, number>;
  percent_arrived: number;
  median_hours_to_arrival: number | null;
  distribution_days: Record<string, number>;
  aging: { public_id: string; days: number; state: string }[];
  lost_queue: { public_id: string; case_id: number; state: string }[];
  note: string;
};

export default async function FacilityPage() {
  const user = await getSession();
  if (!user) redirect("/login");
  if (!["clinician", "navigator", "program_manager", "admin"].includes(user.role)) redirect("/");
  const data = await api<Summary>("/followup/facility");
  const percent = Math.round(data.percent_arrived * 100);
  const funnel = Object.entries(data.funnel);
  const funnelMax = Math.max(1, ...funnel.map(([, count]) => count));
  const buckets = Object.entries(data.distribution_days);
  const bucketMax = Math.max(1, ...buckets.map(([, count]) => count));

  return (
    <Page>
      <PageHeader
        title="Until they arrive"
        description={data.note}
        meta={
          <>
            <Badge tone="outline">Synthetic</Badge>
            <Badge tone="warn">{sentence(data.review.toLowerCase())}</Badge>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Arrived at a facility"
          value={`${percent}%`}
          detail="Share of issued IDs with an arrival confirmed by facility staff."
          visual={<ProgressRing percent={percent} size={72} label="Arrived" />}
        />
        <MetricCard
          label="Median time to arrival"
          value={data.median_hours_to_arrival == null ? "–" : `${data.median_hours_to_arrival.toFixed(1)}h`}
          detail={
            data.median_hours_to_arrival == null
              ? "Not enough arrivals yet."
              : `From screening to a confirmed arrival, about ${(data.median_hours_to_arrival / 24).toFixed(1)} days.`
          }
        />
        <MetricCard
          label="Screened, not arrived"
          value={data.aging.length}
          detail={`${data.lost_queue.length} of them ${data.lost_queue.length === 1 ? "needs" : "need"} a person to decide what happens next.`}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card as="section" aria-labelledby="funnel-heading">
          <SectionHeader id="funnel-heading" title="Where people are" description="Everyone issued an ID, by their current step." />
          <div className="mt-5 space-y-2.5">
            {funnel.map(([state, count]) => (
              <Meter key={state} label={stageShort(state)} value={count} max={funnelMax} tone={state === "arrived" || state === "with_hospital" ? "deep" : "teal"} />
            ))}
          </div>
        </Card>
        <Card as="section" aria-labelledby="days-heading">
          <SectionHeader id="days-heading" title="Days to arrival" description="How long confirmed arrivals took, in days." />
          <ol className="mt-5 flex h-40 items-end gap-3" aria-label="Arrivals by number of days">
            {buckets.map(([bucket, count]) => (
              <li key={bucket} className="flex h-full flex-1 flex-col items-center justify-end">
                <span className="text-sm font-semibold tabular-nums text-ink">{count}</span>
                <span
                  aria-hidden="true"
                  className="mt-1 w-full rounded-t-lg bg-teal"
                  style={{ height: `${count > 0 ? Math.max(6, (count / bucketMax) * 75) : 2}%` }}
                />
                <span className="mt-2 w-full border-t-2 border-line pt-1.5 text-center text-[0.8125rem] text-ink-2">
                  {bucket} days
                </span>
              </li>
            ))}
          </ol>
        </Card>
      </div>

      <section aria-labelledby="lost-heading" className="space-y-3">
        <SectionHeader
          id="lost-heading"
          title="Needs a person to decide"
          description="Record the arrival if they came, or close as lost. Lost to follow-up is always a human decision."
        />
        {data.lost_queue.length === 0 ? (
          <EmptyState icon={<CircleCheck aria-hidden="true" />} title="No decisions waiting">
            Nobody is waiting for an arrival or lost-to-follow-up decision.
          </EmptyState>
        ) : (
          <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface shadow-raised">
            {data.lost_queue.map((row) => (
              <li key={row.case_id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-[1.0625rem] font-semibold tracking-wide text-ink">{row.public_id}</p>
                  <p className="text-sm text-ink-2">Now: {stageShort(row.state).toLowerCase()}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <form action={markArrived}>
                    <input type="hidden" name="case_id" value={row.case_id} />
                    <SubmitButton size="sm" pendingLabel="Recording">
                      <DoorOpen aria-hidden="true" />
                      Record arrival
                    </SubmitButton>
                  </form>
                  <form action={markLost}>
                    <input type="hidden" name="case_id" value={row.case_id} />
                    <SubmitButton variant="danger" size="sm" pendingLabel="Closing">
                      <UserX aria-hidden="true" />
                      Close as lost
                    </SubmitButton>
                  </form>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="aging-heading" className="space-y-3">
        <SectionHeader id="aging-heading" title="Screened, not yet arrived" description="Longest wait first." />
        {data.aging.length === 0 ? (
          <EmptyState icon={<CircleCheck aria-hidden="true" />} title="Everyone has arrived" />
        ) : (
          <Table caption="People screened who have not arrived yet">
            <THead>
              <Th>ID</Th>
              <Th>Screened</Th>
              <Th>Current step</Th>
            </THead>
            <tbody>
              {data.aging.map((row) => (
                <Tr key={row.public_id}>
                  <Td className="font-medium tracking-wide text-ink">{row.public_id}</Td>
                  <Td>
                    {row.days} {row.days === 1 ? "day" : "days"} ago
                  </Td>
                  <Td>
                    <Badge tone="outline">{stageShort(row.state)}</Badge>
                  </Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </section>
    </Page>
  );
}
