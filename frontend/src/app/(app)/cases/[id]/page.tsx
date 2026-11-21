export const instant = false;
import { notFound } from "next/navigation";
import { CHANNEL_LABEL, fmtStage, fmtTime } from "@/components/OutreachKind";
import {
  Badge,
  Banner,
  Card,
  JourneyStepper,
  Notice,
  Page,
  PageHeader,
  SectionHeader,
  Timeline,
  TimelineItem,
  type Tone,
} from "@/components/ui";
import { STAGES, getCaseDetail, type CaseStatus, type OutreachEvent } from "@/lib/outreach-api";
import { markAttended } from "./actions";
import { AttendedButton } from "./AttendedButton";

const STATUS: Record<CaseStatus, { label: string; blurb: string; tone: Tone }> = {
  on_track: { label: "On track", blurb: "Within the expected timeframe for this stage.", tone: "teal" },
  overdue: { label: "Overdue", blurb: "Past the target timeframe. Automated outreach is in progress.", tone: "warn" },
  escalated: {
    label: "Escalated",
    blurb: "Automated outreach is exhausted. A care coordinator needs to step in.",
    tone: "danger",
  },
  closed: { label: "Closed", blurb: "This case has finished the pathway.", tone: "neutral" },
};

function eventTitle(e: OutreachEvent): string {
  if (e.kind === "response") {
    return `Patient attended (after ${e.attempt} outreach contact${e.attempt === 1 ? "" : "s"})`;
  }
  if (e.kind === "escalation") return `Escalated to a care coordinator, attempt ${e.attempt}`;
  return `${CHANNEL_LABEL[e.channel]}, attempt ${e.attempt}`;
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
  const justAttended = attended && (STAGES as readonly string[]).includes(attended) ? attended : null;

  return (
    <Page>
      <PageHeader
        back={{ href: "/outreach", label: "Follow-up ladder" }}
        title={`Case ${c.id}`}
        description={
          <>
            {s.blurb} In {fmtStage(c.stage).toLowerCase()} since{" "}
            <time dateTime={c.stage_entered_at}>{fmtTime(c.stage_entered_at)} UTC</time>.
          </>
        }
        meta={
          <>
            <Badge tone="outline">{c.patient_ref}</Badge>
            <Badge tone={s.tone}>{s.label}</Badge>
          </>
        }
      />

      <Banner>
        Synthetic data only. Contacts are simulated; nothing is actually sent. Pathway timings are unreviewed placeholders
        pending clinical review.
      </Banner>

      {justAttended ? (
        <Notice tone="ok" title="Loop closed">
          The patient attended and the case moved to {fmtStage(justAttended).toLowerCase()}. The outreach ladder has been
          reset for this stage.
        </Notice>
      ) : null}

      <Card as="section" aria-labelledby="progress-heading">
        <h2 id="progress-heading" className="sr-only">
          Pathway progress
        </h2>
        <JourneyStepper
          label="Care pathway stages"
          steps={STAGES.map((stage) => ({ id: stage, label: fmtStage(stage) }))}
          current={c.stage}
          finished={status === "closed"}
        />
      </Card>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)]">
        <Card as="section" aria-labelledby="action-heading">
          <SectionHeader
            id="action-heading"
            title="Record patient attendance"
            description={
              nextStages.length === 0
                ? "This case is closed. No further action is needed."
                : nextStages.length > 1
                  ? "The next step depends on the outcome of the visit. Choose one."
                  : "Confirm that the patient attended. The case will advance and the outreach ladder will reset."
            }
          />
          {nextStages.length > 0 ? (
            <div className="mt-5 flex flex-wrap gap-3">
              {nextStages.map((next) => (
                <form key={next} action={markAttended}>
                  <input type="hidden" name="caseId" value={c.id} />
                  <input type="hidden" name="toStage" value={next} />
                  <AttendedButton label={`Attended, move to ${fmtStage(next).toLowerCase()}`} />
                </form>
              ))}
            </div>
          ) : null}
        </Card>

        <Card as="section" aria-labelledby="timeline-heading">
          <SectionHeader id="timeline-heading" title="Outreach timeline" description="Times are UTC." />
          <div className="mt-5">
            {events.length === 0 ? (
              <p className="text-sm text-ink-2">No outreach recorded yet.</p>
            ) : (
              <Timeline label="Outreach contacts">
                {events.map((e) => (
                  <TimelineItem
                    key={e.id}
                    tone={e.kind === "response" ? "ok" : e.kind === "escalation" ? "danger" : "default"}
                    title={eventTitle(e)}
                    meta={
                      <>
                        <time dateTime={e.created_at}>{fmtTime(e.created_at)}</time>, {fmtStage(e.stage).toLowerCase()} stage
                      </>
                    }
                  >
                    <span className="text-ink-2">{e.message}</span>
                  </TimelineItem>
                ))}
              </Timeline>
            )}
          </div>
        </Card>
      </div>
    </Page>
  );
}
